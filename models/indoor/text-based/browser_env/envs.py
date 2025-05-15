import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

import numpy as np
import numpy.typing as npt
from beartype import beartype
from beartype.door import is_bearable
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
            case "html" | "accessibility_tree":
                self.text_observation_type = observation_type
                self.image_observation_type = ""
                self.main_observation_type = "text"
            case "image":
                self.image_observation_type = observation_type
                self.text_observation_type = ""  # type: ignore[assignment]
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

        storage_state = instance_config.get("storage_state", None)
        start_url = instance_config.get("start_url", None)
        geolocation = instance_config.get("geolocation", None)

        self.context = self.browser.new_context(
            viewport=self.viewport_size,
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
                client = page.context.new_cdp_session(
                    page
                )  # talk to chrome devtools
                if self.text_observation_type == "accessibility_tree":
                    client.send("Accessibility.enable")
                page.client = client  # type: ignore # TODO[shuyanzh], fix this hackey client
                page.goto(url)
            # set the first page as the current page
            self.page = self.context.pages[0]
            self.page.bring_to_front()
        else:
            self.page = self.context.new_page()
            client = self.page.context.new_cdp_session(self.page)
            if self.text_observation_type == "accessibility_tree":
                client.send("Accessibility.enable")
            self.page.client = client  # type: ignore

    def get_page_client(self, page: Page) -> CDPSession:
        return page.client  # type: ignore

    def _get_obs(self) -> dict[str, Observation]:
        obs = self.observation_handler.get_observation(
            self.page, self.get_page_client(self.page)
        )
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

        if self.sleep_after_execution > 0:
            time.sleep(self.sleep_after_execution)

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
            )
            success = True
        except Exception as e:
            fail_error = str(e)

        # hard sleep TODO[shuyanzh] suboptimal, may need to check network
        if self.sleep_after_execution > 0:
            time.sleep(self.sleep_after_execution)

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

        observation = self.get_obs()
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
            observation = self.get_obs()
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

        observation = self.get_obs()
        info = [success, str(error)]
        
        msg = (
            observation,
            float(success),  # success
            termination,  # terminated
            False,  # truncated
            info,
        )
        return msg
    
    def get_obs(self):
        return self.filter_object_data(self.event.metadata["objects"])

    def process_value(self, value):
        """
        Process a single value:
        - Round numbers to 1 decimal
        - Convert true/false to yes/no
        - Return None for null values to be filtered out later
        """
        if value is None:
            return None
        if isinstance(value, float):
            return round(value, 1)
        elif isinstance(value, bool):
            return "yes" if value else "no"
        return value

    def remove_fields_and_round(self, obj):
        """
        Remove specified fields, null values, round numbers, and convert booleans.
        Also rename axisAlignedBoundingBox to bbox.
        """
        if isinstance(obj, dict):
            # Fields to remove - expanded list based on requirements
            fields_to_remove = [
                'objectOrientedBoundingBox', 'rotation', 'position', 'cornerPoints',
                'size', 'visible', 'isInteractable', 'breakable', 'isBroken',
                'openable', 'isOpen', 'openness', 'pickupable', 'isPickedUp',
                'moveable', 'mass', 'objectType', 'objectId', 'isMoving',
                'controlledObjects', 'assetId', 'fillLiquid',
                # Added fields to remove as per requirements
                'isColdSource', 'temperature', 'isHeatSource', 
                'receptacle', 'isToggled', 'isDirty',
                'canBeUsedUp', 'isUsedUp', 'salientMaterials',
                'canFillWithLiquid', 'isFilledWithLiquid', 'receptacleObjectIds'
            ]
            
            # Also remove any field that ends with "able"
            able_fields = [key for key in obj.keys() if key.endswith('able')]
            fields_to_remove.extend(able_fields)
            
            # Check if salientMaterials is not ['Food'] - if so, add isCooked and isSliced to fields to remove
            salient_materials = obj.get('salientMaterials', [])
            if not (isinstance(salient_materials, list) and len(salient_materials) == 1 and salient_materials[0] == 'Food'):
                fields_to_remove.extend(['isCooked', 'isSliced'])
            
            # Create new dict without unwanted fields and with processed values
            new_obj = {}
            for key, value in obj.items():
                if key not in fields_to_remove:
                    # Special handling for name - extract part before underscore
                    if key == 'name' and isinstance(value, str) and '_' in value:
                        value = value.split('_')[0]
                    
                    # Special handling for parentReceptacles
                    if key == 'parentReceptacles' and isinstance(value, list):
                        new_value = []
                        for item in value:
                            if isinstance(item, str) and '|' in item:
                                # Extract 'Floor' from 'Floor|+00.00|+00.00|+00.00'
                                new_value.append(item.split('|')[0])
                            else:
                                new_value.append(item)
                        processed_value = new_value
                    # Process other values
                    elif isinstance(value, dict):
                        processed_value = self.remove_fields_and_round(value)
                    elif isinstance(value, list):
                        processed_value = [
                            item for item in (self.remove_fields_and_round(x) for x in value)
                            if item is not None
                        ]
                    else:
                        processed_value = self.process_value(value)
                    
                    # Only add non-null values
                    if processed_value is not None and processed_value != []:
                        # Rename axisAlignedBoundingBox to bbox
                        new_key = 'bbox' if key == 'axisAlignedBoundingBox' else key
                        new_obj[new_key] = processed_value
                        
            return new_obj
        
        elif isinstance(obj, list):
            processed_list = [
                item for item in (self.remove_fields_and_round(x) for x in obj)
                if item is not None
            ]
            return processed_list if processed_list else None
        else:
            return self.process_value(obj)

    def should_keep_object(self, obj):
        """
        Keep object if:
        1. Not a Drawer/CounterTop/Cabinet AND
        2. Either:
            - is a functional object
        
        Note: Modified to exclude the old criteria since many of those fields
        are now being removed
        """
        # Check if it's one of the excluded object types first
        obj_name = obj.get('name', '')
        if any(excluded in obj_name for excluded in ['Drawer', 'CounterTop', 'Cabinet']):
            return False
        
        # Always keep objects that have a distance and bbox
        return 'distance' in obj and 'bbox' in obj

    def filter_object_data(self, data):
        """
        1. Filter objects based on criteria (excluding Drawer/CounterTop/Cabinet)
        2. Remove specified fields and null values
        3. Round numbers to 1 decimal
        4. Convert boolean values to yes/no
        5. Rename axisAlignedBoundingBox to bbox
        6. Remove newlines and extra spaces
        7. Process name and parentReceptacles as specified
        8. Group objects with the same name
        9. Consolidate isSliced and isCooked values within groups
        """
        processed_objects = []
        
        # Process each object first
        for obj in data:
            try:
                processed_obj = self.remove_fields_and_round(obj)
                if processed_obj:  # Only add if not None
                    processed_objects.append(processed_obj)
            except Exception as e:
                print(f"Warning: Error processing object: {e}")
                continue
        
        # Group objects by name
        object_groups = {}
        for obj in processed_objects:
            name = obj.get('name')
            if name:
                if name not in object_groups:
                    object_groups[name] = []
                object_groups[name].append(obj)
        
        # Consolidate isSliced and isCooked values within each group
        final_data = []
        for name, group in object_groups.items():
            if len(group) == 1:
                # If only one object with this name, add it directly
                final_data.append(group[0])
            else:
                # For multiple objects with the same name, consolidate properties
                is_sliced = False
                is_cooked = False
                
                # Check if any object has isSliced or isCooked set to "yes"
                for obj in group:
                    if obj.get('isSliced') == "yes":
                        is_sliced = True
                    if obj.get('isCooked') == "yes":
                        is_cooked = True
                
                # Use the first object as a template and update properties
                consolidated_obj = group[0].copy()
                if is_sliced:
                    consolidated_obj['isSliced'] = "yes"
                if is_cooked:
                    consolidated_obj['isCooked'] = "yes"
                
                final_data.append(consolidated_obj)
        
        return final_data