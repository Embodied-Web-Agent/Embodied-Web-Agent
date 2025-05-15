"""Script to run end-to-end evaluation on the benchmark"""
import argparse
import glob
import json
import logging
import os
import random
import subprocess
import tempfile
import time
from pathlib import Path
import numpy as np

import openai

from agent import (
    Agent,
    PromptAgent,
    TeacherForcingAgent,
    construct_agent,
)
from agent.prompts import *
from browser_env import (
    Action,
    ActionTypes,
    ScriptBrowserEnv,
    AI2ThorEnv,
    StateInfo,
    Trajectory,
    create_stop_action,
)
from browser_env.actions import is_equivalent
from browser_env.auto_login import get_site_comb_from_filepath
from browser_env.helper_functions import (
    RenderHelper,
    get_action_description,
)
from evaluation_harness import evaluator_router

LOG_FOLDER = "log_files"
Path(LOG_FOLDER).mkdir(parents=True, exist_ok=True)
LOG_FILE_NAME = f"{LOG_FOLDER}/log_{time.strftime('%Y%m%d%H%M%S', time.localtime())}_{random.randint(0, 10000)}.log"

logger = logging.getLogger("logger")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

file_handler = logging.FileHandler(LOG_FILE_NAME)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

# Set the log format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)


def config() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run end-to-end evaluation on the benchmark"
    )
    parser.add_argument(
        "--render", action="store_true", help="Render the browser"
    )
    parser.add_argument(
        "--slow_mo",
        type=int,
        default=0,
        help="Slow down the browser by the specified amount",
    )
    parser.add_argument(
        "--action_set_tag", default="id_accessibility_tree", help="Action type"
    )
    parser.add_argument(
        "--observation_type",
        choices=["accessibility_tree", "html", "image"],
        default="accessibility_tree",
        help="Observation type",
    )
    parser.add_argument(
        "--current_viewport_only",
        action="store_true",
        help="Only use the current viewport for the observation",
    )
    parser.add_argument("--viewport_width", type=int, default=1280)
    parser.add_argument("--viewport_height", type=int, default=720)
    parser.add_argument("--save_trace_enabled", action="store_true")
    parser.add_argument("--sleep_after_execution", type=float, default=0.0)

    parser.add_argument("--max_steps", type=int, default=40)

    # agent config
    parser.add_argument("--agent_type", type=str, default="prompt")
    parser.add_argument(
        "--instruction_path",
        type=str,
        default="agents/prompts/state_action_agent.json",
    )
    parser.add_argument(
        "--parsing_failure_th",
        help="When concesecutive parsing failure exceeds this threshold, the agent will stop",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--repeating_action_failure_th",
        help="When concesecutive repeating action exceeds this threshold, the agent will stop",
        type=int,
        default=3,
    )

    # lm config
    parser.add_argument("--provider", type=str, default="openai")
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo-0613")
    parser.add_argument("--mode", type=str, default="chat")
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--top_p", type=float, default=1.0)
    parser.add_argument("--context_length", type=int, default=0)
    parser.add_argument("--max_tokens", type=int, default=384)
    parser.add_argument("--stop_token", type=str, default=None)
    parser.add_argument(
        "--max_retry",
        type=int,
        help="max retry times to perform generations when parsing fails",
        default=1,
    )
    parser.add_argument(
        "--max_obs_length",
        type=int,
        help="when not zero, will truncate the observation to this length before feeding to the model",
        default=1920,
    )
    parser.add_argument(
        "--model_endpoint",
        help="huggingface model endpoint",
        type=str,
        default="",
    )

    # example config
    parser.add_argument("--test_start_idx", type=int, default=0)
    parser.add_argument("--test_end_idx", type=int, default=1000)

    # logging related
    parser.add_argument("--result_dir", type=str, default="")
    args = parser.parse_args()

    # check the whether the action space is compatible with the observation space
    if (
        args.action_set_tag == "id_accessibility_tree"
        and args.observation_type != "accessibility_tree"
    ):
        raise ValueError(
            f"Action type {args.action_set_tag} is incompatible with the observation type {args.observation_type}"
        )

    return args

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle numpy arrays
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        # Handle DetachedPage or similar (fallback to text or str)
        if obj.__class__.__name__ == "DetachedPage":
            try:
                return obj.get_text()  # If it has get_text()
            except Exception:
                return str(obj)

        # Handle other non-serializable types gracefully
        return super().default(obj)
    
def early_stop(
    trajectory: Trajectory, max_steps: int, environment: str, thresholds: dict[str, int]
) -> tuple[bool, str]:
    """Check whether need to early stop"""

    # reach the max step
    num_steps = (len(trajectory) - 1) / 2
    if num_steps >= max_steps:
        return True, f"Reach max steps {max_steps}"

    k = 5
    last_k_actions = trajectory[1::2][-k:] 

    if all(
            [
                "witch" in action
                for action in last_k_actions
            ]
        ) and len(last_k_actions) >= 5:
        print (f"Stuck in switch for {k} times")

        return True, f"Stuck in switch for {k} times"


    k = thresholds["parsing_failure"]
    action_seq = trajectory[1::2]  # type: ignore[assignment]
    last_k_actions = trajectory[1::2][-k:] 

    if environment == "Web" and len(action_seq) and len(action_seq) and (not isinstance(action_seq[-1], str)):
        # Case: parsing failure for k times        
         # type: ignore[assignment]
        if len(last_k_actions) >= k:
            if all(
                [
                    (not isinstance(action, str)) and action["action_type"] == ActionTypes.NONE
                    for action in last_k_actions
                ]
            ):
                print (f"Failed to parse web actions for {k} times")

                return True, f"Failed to parse web actions for {k} times"
    # else:
    #     last_k_states = trajectory[0::2][-k:]  # type: ignore[assignment]
    #     if len(last_k_states) >= k:
    #         if all(
    #             [
    #                 state["environment"] == "Embodied" and state["embodied_info"][0] == False
    #                 for state in last_k_states
    #             ]
    #         ):
    #             return True, f"Failed to execute embodied actions for {k} times"

    # Case: same action for k times
    k = thresholds["repeating_action"]
    last_k_actions = trajectory[1::2][-k:]  # type: ignore[assignment]

    if len(action_seq) == 0:
        return False, ""

    last_action = action_seq[-1]

    if environment == "Web" and len(action_seq) and (not isinstance(action_seq[-1], str)):
        if last_action["action_type"] != ActionTypes.TYPE:
            pass
            # if len(last_k_actions) >= k:
            #     if all(
            #         [
            #             (not isinstance(action, str)) and is_equivalent(action, last_action)
            #             for action in last_k_actions
            #         ]
            #     ):
            #         return True, f"Same action for {k} times"
        else:
            pass
            # check the action sequence
            # k = 5
            # if (
            #     sum([(not isinstance(action, str)) and is_equivalent(action, last_action) for action in action_seq])
            #     >= k
            # ):
            #     print (f"Same typing action for {k} times")
            #     return True, f"Same typing action for {k} times"
    else:
        k = 10
        if (
                sum([action == last_action for action in action_seq])
                >= k
            ):
                print (f"Same embodied action for {k} times")
                return True, f"Same embodied action for {k} times"

    return False, ""


def test(
    args: argparse.Namespace,
    agent: Agent | PromptAgent | TeacherForcingAgent,
    config_file_list: list[str],
) -> None:
    scores = []
    max_steps = args.max_steps

    #TODO: early_stop
    early_stop_thresholds = {
        "parsing_failure": args.parsing_failure_th,
        "repeating_action": args.repeating_action_failure_th,
    }

    web_env = ScriptBrowserEnv(
        headless=not args.render,
        slow_mo=args.slow_mo,
        observation_type=args.observation_type,
        current_viewport_only=args.current_viewport_only,
        viewport_size={
            "width": args.viewport_width,
            "height": args.viewport_height,
        },
        save_trace_enabled=args.save_trace_enabled,
        sleep_after_execution=args.sleep_after_execution,
    )

    embodied_env = AI2ThorEnv(
        scene = "FloorPlan1"
    )
    

    for config_file in config_file_list:
        observations = []
        results = dict()
        try:
        # if True:
            render_helper = RenderHelper(
                config_file, args.result_dir, args.action_set_tag
            )

            # get intent
            with open(config_file) as f:
                _c = json.load(f)
                intent = _c["intent"]
                task_id = _c["task_id"]

                embodied_obs, embodied_info = embodied_env.reset(_c["scene"], _c["Object Final States"])
                
                # automatically login
                if _c["storage_state"]:
                    cookie_file_name = os.path.basename(_c["storage_state"])
                    comb = get_site_comb_from_filepath(cookie_file_name)
                    temp_dir = tempfile.mkdtemp()
                    # subprocess to renew the cookie
                    subprocess.run(
                        [
                            "python",
                            "browser_env/auto_login.py",
                            "--auth_folder",
                            temp_dir,
                            "--site_list",
                            *comb,
                        ]
                    )
                    _c["storage_state"] = f"{temp_dir}/{cookie_file_name}"
                    assert os.path.exists(_c["storage_state"])
                    # update the config file
                    config_file = f"{temp_dir}/{os.path.basename(config_file)}"
                    with open(config_file, "w") as f:
                        json.dump(_c, f)

            logger.info(f"[Config file]: {config_file}")
            logger.info(f"[Intent]: {intent}")

            agent.reset(config_file)
            trajectory: Trajectory = []
            web_obs, web_info = web_env.reset(options={"config_file": config_file})
            
            # embodied_obs, embodied_info = embodied_env.reset()
            
            state_info: StateInfo = {"web_observation": web_obs, "web_info": web_info, "embodied_observation": embodied_obs, "embodied_info": embodied_info}
            state_info["environment"] = "Web"
            trajectory.append(state_info)
            

            # action = "Teleport [Potato]"
            # embodied_obs, _, terminated, _, embodied_info = embodied_env.step(action)
            
            # action = "SliceObject [Potato]"
            # embodied_obs, _, terminated, _, embodied_info = embodied_env.step(action)

            # action = "CookObject [Potato]"
            # embodied_obs, _, terminated, _, embodied_info = embodied_env.step(action)
            
            # # state_info: StateInfo = {"observation": web_obs, "info": web_info, "embodied_observation": embodied_obs, "embodied_info": embodied_info}
            # # trajectory.append(state_info)

            meta_data = {"action_history": ["None"]}
            meta_data["current_round_embodied_history"] = []
            meta_data["current_shopping_history"] = []
            shopping_history = None

            environment = "Web"

            buying_status = False

            while True:
                #TODO: early_stop
                early_stop_flag, stop_info = early_stop(
                    trajectory, max_steps, environment, early_stop_thresholds
                )

                if early_stop_flag:
                    trajectory.append(create_stop_action(f"Early stop: {stop_info}"))
                    trajectory.append(action)
                    break
                else:
                    try:
                    # if True:
                        action = agent.next_action(
                            trajectory, intent, environment=environment, meta_data=meta_data
                        )

                    except ValueError as e:
                        # get the error message
                        action = create_stop_action(f"ERROR: {str(e)}")
                        trajectory.append(action)
                        break

                trajectory.append(action)

                if isinstance(action, str) and action.split()[0] == "Buy":
                    environment = "Web"
                    meta_data["shopping"] = action
                    meta_data["shopping_actions"] = []
                    trajectory.append(trajectory[-2])
                    buying_status = True
                    continue

                if isinstance(action, str) and action.split()[0] == "Bought":
                    environment = "Web"
                    try:
                        del meta_data["shopping"]
                        del meta_data["shopping_actions"]
                    except:
                        pass
                    trajectory.append(trajectory[-2])
                    buying_status = False
                    continue

                if isinstance(action, str) and action.split()[0] == "switch_environment":
                    print ("Switching Environment")
                    trajectory.append(trajectory[-2])

                    if environment == "Web":
                        environment = "Embodied"
                        meta_data["current_round_embodied_history"].append(action)
                    else:
                        environment = "Web"
                        meta_data["current_round_embodied_history"] = []
                        meta_data["action_history"].append(action)
                    continue
                
                try:
                    if environment == "Web":
                        action_str = get_action_description(
                            action,
                            state_info["web_info"]["observation_metadata"],
                            action_set_tag=args.action_set_tag,
                            prompt_constructor=agent.prompt_constructor
                            if isinstance(agent, PromptAgent)
                            else None,
                        )
                        render_helper.render(
                            action, state_info, meta_data, args.render_screenshot
                        )
                        if buying_status:
                            meta_data["shopping_actions"].append(action_str)
                            shopping_history = meta_data["shopping_actions"]

                        meta_data["action_history"].append(action_str)

                        obs, _, terminated, _, info = web_env.step(action)

                        state_info: StateInfo = {"web_observation": obs, "web_info": info}
                        state_info["embodied_observation"] = trajectory[-2]["embodied_observation"]
                        state_info["embodied_info"] = trajectory[-2]["embodied_info"]
                        state_info["environment"] = "Web"
                        trajectory.append(state_info)
                        observations.append(obs["text"])
                        
                    else:
                        obs, _, terminated, _, info = embodied_env.step(action)

                        state_info: StateInfo = {"embodied_observation": obs, "embodied_info": info}
                        state_info["web_observation"] = trajectory[-2]["web_observation"]
                        state_info["web_info"] = trajectory[-2]["web_info"]
                        state_info["environment"] = "Embodied"
                        trajectory.append(state_info)
                        observations.append(obs)

                        meta_data["current_round_embodied_history"].append(action)

                        meta_data["last_action_success"] = info

                        if terminated:
                            print ("terminated")
                            # add a action place holder
                            trajectory.append("score 1.0.")
                            break
                except:
                    trajectory.pop()
                
        except openai.error.OpenAIError as e:
            logger.info(f"[OpenAI Error] {repr(e)}")
        except Exception as e:
            logger.info(f"[Unhandled Error] {repr(e)}]")
            import traceback

            # write to error file
            with open(Path(args.result_dir) / "error.txt", "a") as f:
                f.write(f"[Config file]: {config_file}\n")
                f.write(f"[Unhandled Error] {repr(e)}\n")
                f.write(traceback.format_exc())  # write stack trace to file

        score, states = embodied_env.state_evaluator()
        results = {"score": score, "state_evaluator": states, "actions": trajectory[1::2], "observations": observations, "shopping_history": shopping_history}

        with open(f"results/{config_file.split('/')[-1]}_record.json", "w") as f:
            json.dump(results, f, cls=CustomEncoder)

        scores.append(score)

        logger.info(f"[Result] {config_file} score: {score}")

        if args.save_trace_enabled:
            web_env.save_trace(
                Path(args.result_dir) / "traces" / f"{task_id}.zip"
            )

        render_helper.close()

    final_score = sum(scores) / len(scores)
    print (f"[Final Score] {final_score}")

    web_env.close()
    logger.info(f"Average score: {sum(scores) / len(scores)}")


def prepare(args: argparse.Namespace) -> None:
    # convert prompt python files to json
    from agent.prompts import to_json

    to_json.run()

    # prepare result dir
    result_dir = args.result_dir
    if not result_dir:
        result_dir = (
            f"cache/results_{time.strftime('%Y%m%d%H%M%S', time.localtime())}"
        )
    if not Path(result_dir).exists():
        Path(result_dir).mkdir(parents=True, exist_ok=True)
        args.result_dir = result_dir
        logger.info(f"Create result dir: {result_dir}")

    if not (Path(result_dir) / "traces").exists():
        (Path(result_dir) / "traces").mkdir(parents=True)

    # log the log file
    with open(os.path.join(result_dir, "log_files.txt"), "a+") as f:
        f.write(f"{LOG_FILE_NAME}\n")


def get_unfinished(config_files: list[str], result_dir: str) -> list[str]:
    result_files = glob.glob(f"{result_dir}/*.html")
    task_ids = [
        os.path.basename(f).split(".")[0].split("_")[1] for f in result_files
    ]
    unfinished_configs = []
    for config_file in config_files:
        task_id = os.path.basename(config_file).split(".")[0]
        if task_id not in task_ids:
            unfinished_configs.append(config_file)
    return unfinished_configs


def dump_config(args: argparse.Namespace) -> None:
    config_file = Path(args.result_dir) / "config.json"
    if not config_file.exists():
        with open(config_file, "w") as f:
            json.dump(vars(args), f, indent=4)
            logger.info(f"Dump config to {config_file}")


if __name__ == "__main__":
    args = config()
    args.sleep_after_execution = 2.0
    prepare(args)

    test_file_list = []
    st_idx = args.test_start_idx
    ed_idx = args.test_end_idx
    for i in range(st_idx, ed_idx):
        test_file_list.append(f"config_files/{i}.json")
    if "debug" not in args.result_dir:
        test_file_list = get_unfinished(test_file_list, args.result_dir)

    if len(test_file_list) == 0:
        logger.info("No task left to run")
    else:
        print(f"Total {len(test_file_list)} tasks left")
        args.render = False
        args.render_screenshot = True
        args.save_trace_enabled = True

        args.current_viewport_only = True
        dump_config(args)

        agent = construct_agent(args)
        test(args, agent, test_file_list)
