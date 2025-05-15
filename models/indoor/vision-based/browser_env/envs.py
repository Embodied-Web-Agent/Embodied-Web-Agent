import json
import os
import re
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

import numpy as np
import numpy.typing as npt
import requests
from beartype import beartype
from gymnasium import Env
from gymnasium.spaces import Box, Text
from playwright.sync_api import (
    CDPSession,
    Page,
    Playwright,
    ViewportSize,
    expect,
    sync_playwright,
)

DATASET = os.environ["DATASET"]
if DATASET == "visualwebarena":
    from browser_env.env_config import (
        CLASSIFIEDS,
        CLASSIFIEDS_RESET_TOKEN,
    )

from .actions import Action, execute_action, get_action_space
from .processors import ObservationHandler, ObservationMetadata
from .utils import (
    AccessibilityTree,
    DetachedPage,
    Observation,
    png_bytes_to_numpy,
)

from ai2thor.controller import Controller

@dataclass
class PlaywrightScript:
    function: str  # goto, get_by_role
    destination: str  # https://www.google.com/, combobox
    name: str | None = None  # Search, Avatar 2009
    operation: str | None = None  # click, fill, press
    value: str | None = None  # avatar movie, Enter


def parse_action(action: str) -> PlaywrightScript:
    splitted = action.strip().split(" ")
    assert len(splitted) >= 2
    match splitted[:2]:
        case ["goto", url]:
            assert len(splitted) == 2
            return PlaywrightScript("goto", url)
        case ["get_by_role", destination]:
            assert len(splitted) >= 4
            match splitted[2:]:
                case [name, operation]:
                    return PlaywrightScript(
                        "get_by_role", destination, name, operation
                    )
                case [name, operation, value]:
                    return PlaywrightScript(
                        "get_by_role", destination, name, operation, value
                    )
                case _:
                    raise ValueError("Invalid action")
        case _:
            raise ValueError(f"Invalid action {action}")


class ScriptBrowserEnv(Env[dict[str, Observation], Action]):
    """
    The goal of this environment is to produce a prototype of a browser environment.
    In the end, we want to support a fully configurable browser environment with wide
    range of action spaces and observation spaces, both structured and unstructured.
    But in this prototype, we just support action space specified by Playwright script,
    and observation space is the html content of the page.
    """

    @beartype
    def __init__(
        self,
        max_page_length: int = 8192,
        headless: bool = True,
        slow_mo: int = 0,
        observation_type: str = "html",
        current_viewport_only: bool = False,
        viewport_size: ViewportSize = {"width": 1280, "height": 720},
        save_trace_enabled: bool = False,
        sleep_after_execution: float = 0.0,
        captioning_fn=None,
    ):
        # TODO: make Space[Action] = ActionSpace
        self.action_space = get_action_space()  # type: ignore[assignment]
        self.headless = headless
        self.slow_mo = slow_mo
        self.current_viewport_only = current_viewport_only
        self.reset_finished = False
        self.viewport_size = viewport_size
        self.save_trace_enabled = save_trace_enabled
        self.sleep_after_execution = sleep_after_execution

        match observation_type:
            case "html" | "accessibility_tree" | "accessibility_tree_with_captioner":
                self.text_observation_type = observation_type
                self.image_observation_type = ""
                self.main_observation_type = "text"
            case "image":
                self.image_observation_type = observation_type
                self.text_observation_type = ""  # type: ignore[assignment]
                self.main_observation_type = "image"
            case "image_som":
                self.image_observation_type = observation_type
                self.text_observation_type = observation_type  # type: ignore[assignment]
                self.main_observation_type = "image"
            case _:
                raise ValueError(
                    f"Unsupported observation type: {observation_type}"
                )

        self.observation_handler = ObservationHandler(
            self.main_observation_type,
            self.text_observation_type,
            self.image_observation_type,
            self.current_viewport_only,
            self.viewport_size,
            captioning_fn,
        )

        self.observation_space = (
            self.observation_handler.get_observation_space()
        )

    @beartype
    def setup(self, config_file: Path | None = None) -> None:
        self.context_manager = sync_playwright()
        self.playwright = self.context_manager.__enter__()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless, slow_mo=self.slow_mo
        )

        if config_file:
            with open(config_file, "r") as f:
                instance_config = json.load(f)
        else:
            instance_config = {}

        # Reset site if needed. Currently only supported for Classifieds.
        # TODO(jykoh): Add reset functionality for Shopping/Reddit.
        if instance_config.get("require_reset", False):
            if "classifieds" in instance_config["sites"]:
                # Send POST request to __CLASSIFIEDS__/index.php?page=reset with token=CLASSIFIEDS_TOKEN
                response = requests.post(
                    f"{CLASSIFIEDS}/index.php?page=reset",
                    data={"token": CLASSIFIEDS_RESET_TOKEN},
                )

                # Check if the request was successful
                if response.status_code == 200:
                    print("Reset Classifieds site.")
                else:
                    print(
                        "Failed to reset Classifieds site:",
                        response.status_code,
                    )
            else:
                print(
                    "WARNING: Reset is not supported for this site. Please manually reset the site."
                )

        storage_state = instance_config.get("storage_state", None)
        start_url = instance_config.get("start_url", None)
        geolocation = instance_config.get("geolocation", None)

        # Use custom viewport size if specified in the config, otherwise use the default.
        viewport_size = self.viewport_size.copy()
        viewport_size.update(instance_config.get("viewport_size", {}))
        self.observation_handler.viewport_size = viewport_size

        self.context = self.browser.new_context(
            viewport=viewport_size,
            storage_state=storage_state,
            geolocation=geolocation,
            device_scale_factor=1,
        )
        if self.save_trace_enabled:
            self.context.tracing.start(screenshots=True, snapshots=True)

        if start_url:
            start_urls = start_url.split(" |AND| ")
            for url in start_urls:
                page = self.context.new_page()
                if self.text_observation_type in [
                    "accessibility_tree",
                    "accessibility_tree_with_captioner",
                ]:
                    client = page.context.new_cdp_session(page)
                    client.send("Accessibility.enable")
                    client.detach()
                page.goto(url)
            # set the first page as the current page
            self.page = self.context.pages[0]
            self.page.bring_to_front()
        else:
            self.page = self.context.new_page()
            if self.text_observation_type in [
                "accessibility_tree",
                "accessibility_tree_with_captioner",
            ]:
                client = self.page.context.new_cdp_session(self.page)
                client.send("Accessibility.enable")
                client.detach()

    def _get_obs(self) -> dict[str, Observation]:
        obs = self.observation_handler.get_observation(self.page)
        return obs

    def _get_obs_metadata(self) -> dict[str, ObservationMetadata]:
        metadata = self.observation_handler.get_observation_metadata()
        return metadata

    @beartype
    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, str] | None = None,
    ) -> tuple[dict[str, Observation], dict[str, Any]]:
        """
        Reset the environment.
        :param options: options for the environment. The current supported options are:
            - "storage_state": the storage state of the browser. It is a file path to a json file.
        """
        super().reset(seed=seed, options=options)
        if self.reset_finished:
            self.context_manager.__exit__()

        if options is not None and "config_file" in options:
            config_file = Path(options["config_file"])
            if config_file.exists():
                self.setup(config_file=config_file)
            else:
                raise ValueError(f"Config file {config_file} does not exist.")
        else:
            self.setup()
        self.reset_finished = True

        self.page.wait_for_timeout(int(self.sleep_after_execution * 1000))

        observation = self._get_obs()
        observation_metadata = self._get_obs_metadata()
        info = {
            "page": DetachedPage(self.page.url, ""),
            "fail_error": "",
            "observation_metadata": observation_metadata,
        }

        return (observation, info)

    def save_trace(self, trace_path: str | Path) -> None:
        if self.save_trace_enabled:
            self.context.tracing.stop(path=trace_path)

    def close(self) -> None:
        if self.reset_finished:
            self.context_manager.__exit__()

    def step(
        self, action: Action
    ) -> tuple[dict[str, Observation], float, bool, bool, dict[str, Any]]:
        if not self.reset_finished:
            raise RuntimeError("Call reset first before calling step.")

        success = False
        fail_error = ""
        try:
            self.page = execute_action(
                action,
                self.page,
                self.context,
                self.observation_handler.action_processor,
                self.sleep_after_execution,
            )
            success = True
        except Exception as e:
            fail_error = str(e)

        observation = self._get_obs()
        observation_metadata = self._get_obs_metadata()

        info = {
            "page": DetachedPage(self.page.url, self.page.content()),
            "fail_error": fail_error,
            "observation_metadata": observation_metadata,
        }
        msg = (
            observation,
            float(success),  # reward
            False,  # terminated
            False,  # truncated
            info,
        )

        return msg
    
class AI2ThorEnv():
    def __init__(
        self,
        scene=None,
    ):
        self.controller = Controller(
            agentMode="default",
            scene=scene,

            # step sizes
            gridSize=0.25,
            snapToGrid=True,
            rotateStepDegrees=90,

            # image modalities
            renderDepthImage=False,
            renderInstanceSegmentation=False,

            # camera properties
            width=300,
            height=300,
            fieldOfView=90,
            visibilityDistance=25
        )
        self.event = None
        self.ideal_states = None

        print (f"successfully setting up embodied env for scene {scene}")

    def reset(
        self,
        scene,
        ideal_states
    ):
        self.ideal_states = ideal_states
        
        self.controller.reset(
            agentMode="default",
            scene=scene,

            # step sizes
            gridSize=0.25,
            snapToGrid=True,
            rotateStepDegrees=90,

            # image modalities
            renderDepthImage=False,
            renderInstanceSegmentation=False,

            # camera properties
            width=300,
            height=300,
            fieldOfView=90,
            visibilityDistance=25
        )

        self.event = self.controller.step(
            action="InitialRandomSpawn",
            randomSeed=0,
            forceVisible=True,
            numPlacementAttempts=5,
            placeStationary=True
        )

        observation = self.event.frame
        info = self.event.metadata

        return (observation, info)  

    def state_evaluator(
        self,
    ):
        ideal_num = 0
        hit_num = 0
        states = []
            
        for object_statechange in self.ideal_states:
            obj = object_statechange["object"]

            for key, val in object_statechange["changes"].items():                   
                ideal_num += 1
                if key.startswith("is"):
                    for ref_obj in self.event.metadata["objects"]:
                        ref_obj_name = ref_obj["objectId"]
                        if obj.lower() in ref_obj_name.lower():
                            if ref_obj.get(key) == val or (key == "isSliced" and ref_obj.get("isBroken") == val) or (key == "isBroken" and ref_obj.get("isSliced") == val):
                                hit_num += 1
                                states.append([obj, key, val])
                                break
                            
                elif key == "parentReceptacles":
                    find_receptacle = False
                    for ref_obj in self.event.metadata["objects"]:
                        ref_obj_name = ref_obj["objectId"]
                        if obj.lower() in ref_obj_name.lower():
                            try:
                                for obj2 in ref_obj["parentReceptacles"]:
                                    ref_obj_name2 = ref_obj["objectId"]
                                    if ref_obj_name2.split("|")[0].lower() == obj2.lower():
                                        hit_num += 1
                                        states.append([obj, key, val])
                                        find_receptacle = True
                                        break
                            except:
                                pass
                        if find_receptacle:
                            break
                else:
                    print (f"State evaluator not cluding {key}. Please fix.")
        
        return hit_num / ideal_num, states

    # Deprecated  
    def state_evaluator_step(
        self,
    ):
        ideal_num = 0
        hit_num = 0

        for ideal_state in self.ideal_states:
            object_statechanges = ideal_state["objectStateChanges"]
            
            for object_statechange in object_statechanges:
                obj = object_statechange["object"]

                for key, val in object_statechange["changes"].items():                   
                    ideal_num += 1
                    if key.startswith("is"):
                        for ref_obj in self.event.metadata["objects"]:
                            ref_obj_name = ref_obj["objectId"]
                            if obj.lower() in ref_obj_name.lower():
                                if ref_obj.get(key) == val or (key == "isSliced" and ref_obj.get("isBroken") == val) or (key == "isBroken" and ref_obj.get("isSliced") == val):
                                    hit_num += 1
                                    break
                                
                    elif key == "parentReceptacles":
                        find_receptacle = False
                        for ref_obj in self.event.metadata["objects"]:
                            ref_obj_name = ref_obj["objectId"]
                            if obj.lower() in ref_obj_name.lower():
                                for obj2 in ref_obj["parentReceptacles"]:
                                    ref_obj_name2 = ref_obj["objectId"]
                                    if ref_obj_name2.split("|")[0].lower() == obj2.lower():
                                        hit_num += 1
                                        find_receptacle = True
                                        break
                            if find_receptacle:
                                break
                    else:
                        print (f"State evaluator not cluding {key}. Please fix.")
        
        return hit_num / ideal_num
        
    def parse_action(
        self, action
    ):  
        try:
            action, obj = action.split("[")
            action = action.strip()
            obj = obj.strip()
            obj = obj.replace("[", "").replace("]", "")
            original_obj = obj

            target_obj = None
            for ref_obj in self.event.metadata["objects"]:
                ref_obj_name = ref_obj["objectId"]
                if ref_obj_name.split("|")[0].lower() == obj.lower():
                    obj = ref_obj_name
                    target_obj = ref_obj
                    break
            
            kwargs = {}

            # print (self.event.metadata["objects"])
            if target_obj.get("isSliced") or target_obj.get("isBroken"):

                for ref_obj in self.event.metadata["objects"]:
                    ref_obj_name = ref_obj["objectId"]
                    if original_obj.lower() in ref_obj_name.lower() and ("slice" in ref_obj_name.lower() or "cracked" in ref_obj_name.lower()):
                        obj = ref_obj_name
                        break 

            if action == "Teleport":
                self.event = self.controller.step(
                    action="GetInteractablePoses",
                    objectId="Pan|+00.72|+00.90|-02.42"
                )
                
                poses = self.event.metadata["actionReturn"]

                try:
                    kwargs.update({
                        "position": dict(x=poses[0]["x"], y=poses[0]["y"], z=poses[0]["z"]),
                        "rotation": poses[0]["rotation"],
                        "standing": poses[0]["standing"],
                        "horizon": poses[0]["horizon"]
                    })
                    action = "TeleportFull"
                except:
                    error = "The item is not visible. Try to open fridge or cabinets to get it."
                    return "", "", error
            else:
                kwargs.update({"objectId": obj})

            if action == "PickupObject":
                kwargs.update({"forceAction": True, "manualInteract": False})
            elif action == "PutObject":
                kwargs.update({"forceAction": True, "placeStationary": True})
            elif action in ["BreakObject", "OpenObject", "SliceObject", "CookObject"]:
                kwargs.update({"forceAction": True})

            return action, kwargs, ""
        
        except:
            error = "Invalid action or object name. Please check."
            return "", "", error

    def step(
        self, action
    ):
        action, kwargs, error = self.parse_action(action)
        termination = False

        if len(error):
            observation = self.event.frame
            success = False
            info = [success, error]
            
            msg = (
                observation,
                float(success),  # success
                termination,  # terminated
                False,  # truncated
                info,
            )
            return msg
        
        try:
            self.event = self.controller.step(action=action, **kwargs)
            success = self.controller.last_event.metadata["lastActionSuccess"]        
            error = self.controller.last_event.metadata["errorMessage"]
        except Exception as e:
            print(f"Error during controller step: {e}")
            success = False
            error = e

        score = self.state_evaluator()

        if score == 1.0:
            termination = True

        # TODO: change obs to image

        observation = self.event.frame
        info = [success, str(error)]
        
        msg = (
            observation,
            float(success),  # success
            termination,  # terminated
            False,  # truncated
            info,
        )
        return msg
    
