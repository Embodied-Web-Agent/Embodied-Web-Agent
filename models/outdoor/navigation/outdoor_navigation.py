"""
Code to navigate outdoor environments using OCR and VLM.
"""

import json
import time
import argparse
import requests
from openai import OpenAI
from google import genai
from google.genai import types
import base64
import math
from PIL import Image
from io import BytesIO
import re
import os
import math
import logging
from tqdm import tqdm
from pathlib import Path
from prompt.outdoor_navigation import SYSTEM_MSG
from models.outdoor.navigation.utils import calculate_cost, load_environments, compute_heading, get_initial_heading, add_task_ids, haversine, angular_diff, merge_json

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def parse_directions(text):
    """
    Parse textual directions into a list of action-distance dicts.
    Each dict has:
      - "action": one of "left", "right", or "straight"
      - "distance": float distance in meters
    """
    directions = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Strictly skip lines like "2. Reach destination"
        if re.match(r"\d+\.\s*reach destination", line, re.IGNORECASE):
            continue
        # Match "- 169 m" or similar
        m = re.search(r"-?\s*(\d+(?:\.\d+)?)\s*(km|m)\b", line, re.IGNORECASE)
        if not m:
            continue
        value = float(m.group(1))
        unit = m.group(2).lower()
        distance = value * 1000 if unit == "km" else value
        # Determine direction
        lower = line.lower()
        if "left" in lower:
            action = "left"
        elif "right" in lower:
            action = "right"
        else:
            action = "straight"
        directions.append({"action": action, "distance": distance})
    return directions

def fetch_streetview_images(lat, lng, google_api_key):
    """
    Retrieve four street-view images at headings 0, 90, 180, 270 degrees.
    Returns list of raw image bytes.
    """
    images = []
    for heading in [0, 90, 180, 270]:
        url = (
            f"https://maps.googleapis.com/maps/api/streetview"
            f"?size=600x400&location={lat},{lng}"
            f"&heading={heading}&fov=90&pitch=0&key={google_api_key}"
        )
        resp = requests.get(url)
        images.append(resp.content)
        time.sleep(0.1)
    return images

def call_vlm_agent(args: argparse.Namespace, observations='', prompt_text='',  action_prompt='', is_ocr=False, image_path=None):
    """
    Send multimodal prompt (images + text + distance) to VLM and return chosen neighbor ID.
    Or unimodal text-only prompt.
    Or OCR processing.
    """
    if is_ocr:
        if 'gpt' or 'internvl' or 'qwen' in args.model_name:
            # Read image bytes
            with open(image_path, "rb") as img_file:
                img_bytes = img_file.read()
            # Encode image as base64
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            # System instruction for OCR task
            system_msg = {
                "role": "system",
                "content": "You are an expert OCR agent specialized in extracting text from map screenshots, especially navigation instructions."
            }
            # User prompt asking to extract directions
            user_msg = {
                    "role": "user",
                    "content": [
                        { "type": "text", "text": "Please extract all the navigation directions text and ensure that each direction is followed by a corresponding distance from the provided map screenshot. Return only the plain textual directions and distance." },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}",
                            },
                        },
                    ],
                }
            response = client.chat.completions.create(
                model=args.model_name,
                messages=[system_msg, user_msg],
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                top_p=args.top_p
                # attachments=[attachment]
            )
            # Return the agent's extracted directions
            if 'gpt' or 'qwen' in args.model_name:
                usage = response.usage
                logger.debug(f"VLM token usage: prompt_tokens={usage.prompt_tokens}, completion_tokens={usage.completion_tokens}, total_tokens={usage.total_tokens}")
            elif 'internvl' in args.model_name:
                usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
                logger.debug(f"VLM token usage: prompt_tokens={usage['prompt_tokens']}, completion_tokens={usage['completion_tokens']}, total_tokens={usage['total_tokens']}")
            return response.choices[0].message.content.strip(), usage
        elif 'gemini' in args.model_name: # OCR Part
            # https://ai.google.dev/gemini-api/docs/image-understanding#multiple-images
            image_input = Image.open(image_path)
            text_input = "Please extract all the navigation directions text from the provided map screenshot. Return only the plain textual directions."
            response = client.models.generate_content(
                model=args.model_name,
                contents=[image_input, text_input],
                config=types.GenerateContentConfig(
                    system_instruction="You are an expert OCR agent specialized in extracting text from map screenshots, especially navigation instructions.",
                    max_output_tokens=args.max_tokens,
                    temperature=args.temperature,
                    top_p=args.top_p
                )
            )
            usage = response.usage_metadata
            logger.debug(f"VLM token usage: prompt_tokens={usage.prompt_token_count}, completion_tokens={usage.candidates_token_count}, total_tokens={usage.total_token_count}")
            return response.text.strip(), usage
        else:
            raise ValueError(f"Unsupported model: {args.model_name}")

    elif args.multimodal:
        if 'gpt' or 'internvl' or 'qwen' in args.model_name:
            # https://internlm.intern-ai.org.cn/api/document
            system_msg = {"role": "system", "content": SYSTEM_MSG}

            base64_images = [base64.b64encode(img).decode("utf-8") for img in observations]

            attachments = [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
                for img in base64_images
            ]
            user_content_all = [{"type": "text", "text": prompt_text + action_prompt + "\nChoose next node. Reply with exactly one node ID (lat-lng string) on a single line, with no additional commentary"}] + attachments
            user_msg = {"role": "user", "content": user_content_all}

            response = client.chat.completions.create(
                model=args.model_name,
                messages=[system_msg, user_msg],
                # attachments=attachments
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                top_p=args.top_p
            )
            if 'gpt' or 'qwen' in args.model_name:
                usage = response.usage
                logger.debug(f"VLM token usage: prompt_tokens={usage.prompt_tokens}, completion_tokens={usage.completion_tokens}, total_tokens={usage.total_tokens}")
            elif 'internvl' in args.model_name:
                usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
                logger.debug(f"VLM token usage: prompt_tokens={usage['prompt_tokens']}, completion_tokens={usage['completion_tokens']}, total_tokens={usage['total_tokens']}")
            return response.choices[0].message.content.strip(), usage
        elif 'gemini' in args.model_name:
            # https://ai.google.dev/gemini-api/docs/image-understanding#multiple-images
            image_input = Image.open("/path/to/organ.png") # TODO: replace with actual image input
            text_input = prompt_text + action_prompt + "\nChoose next node. Reply with exactly one node ID (lat-lng string) on a single line, with no additional commentary"
            response = client.models.generate_content(
                model=args.model_name,
                contents=[image_input, text_input],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_MSG,
                    max_output_tokens=args.max_tokens,
                    temperature=args.temperature,
                    top_p=args.top_p
                )
            )
            usage = response.usage_metadata
            logger.debug(f"VLM token usage: prompt_tokens={usage.prompt_token_count}, completion_tokens={usage.candidates_token_count}, total_tokens={usage.total_token_count}")
            return response.text.strip(), usage
        else:
            raise ValueError(f"Unsupported model: {args.model_name}")

    else:
        # text-only VLM call
        if "gpt" or "internvl" or "qwen" in args.model_name:
            # https://internlm.intern-ai.org.cn/api/document
            # https://www.alibabacloud.com/help/zh/model-studio/use-qwen-by-calling-api
            system_msg = {"role": "system", "content": SYSTEM_MSG}
            user_msg = {"role": "user", "content": prompt_text + action_prompt + "\nChoose next node. Reply with exactly one node ID (lat-lng string) on a single line, with no additional commentary"}
            response = client.chat.completions.create(
                model=args.model_name, # internvl2.5-latest, qwen-vl-plus
                messages=[system_msg, user_msg],
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                top_p=args.top_p
            )
            choice = response.choices[0].message.content.strip()
            if 'gpt' or 'qwen' in args.model_name:
                usage = response.usage
                logger.debug(f"VLM token usage: prompt_tokens={usage.prompt_tokens}, completion_tokens={usage.completion_tokens}, total_tokens={usage.total_tokens}")
            elif 'internvl' in args.model_name:
                usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
                logger.debug(f"VLM token usage: prompt_tokens={usage['prompt_tokens']}, completion_tokens={usage['completion_tokens']}, total_tokens={usage['total_tokens']}")
            return choice, usage
        elif 'gemini' in args.model_name:
            # https://ai.google.dev/gemini-api/docs/text-generation#system-instructions
                response = client.models.generate_content(
                    model=args.model_name,
                    contents=[prompt_text + action_prompt + "\nChoose next node. Reply with exactly one node ID (lat-lng string) on a single line, with no additional commentary"],
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_MSG,
                        max_output_tokens=args.max_tokens,
                        temperature=args.temperature,
                        top_p=args.top_p
                    )
                )
                usage = response.usage_metadata
                logger.debug(f"VLM token usage: prompt_tokens={usage.prompt_token_count}, completion_tokens={usage.candidates_token_count}, total_tokens={usage.total_token_count}")
                return response.text.strip(), usage
        else:
            raise ValueError(f"Unsupported model: {args.model_name}")

def navigate_environment(args: argparse.Namespace,
                         idx: int, # ! NOTE Should use herustic way to debug and see if the performance is 100% correct
                         env: dict,
                         parsed_directions: list,
                         initial_heading: float) -> dict:
    """
    Navigate through a single environment according to parsed textual directions.
    
    Parameters:
        env (dict): environment with keys "source", "target", "graph"
        parsed_directions (list): list of {"action": str, "distance": float} steps
        initial_heading (float): initial bearing in degrees from true north

    Returns:
        dict: {
            "reached": bool,
            "final_node": str,
            "final_distance_to_target": float,
            "visited": list of str
        }
    """
    graph = env["graph"] # graph is a dict of nodes
    src_key = env["source"] # 40.778445295771355-73.95519516710091
    tgt_key = env["target"] # 40.777989547618326-73.95411775294352

    # parse lat/lng from "lat-lng" keys
    def parse_coord(key):
        lat_str, lng_str = key.split('-')
        return float(lat_str), -float(lng_str) # longitude is negative in the graph since it is in the western hemisphere

    curr = src_key # 40.778445295771355-73.95519516710091
    tlat, tlng = parse_coord(tgt_key)
    # tlng = -tlng  # longitude is negative in the graph since it is in the western hemisphere
    visited = []
    trajectory = []  # Initialize trajectory list

    dir_idx = 0
    remaining = parsed_directions[0]["distance"]
    heading = initial_heading

    for step in range(args.max_steps):
        print(f"Step {step+1} at node {curr}, remaining distance: {remaining:.1f}m")
        # Record current location in trajectory
        lat0 = graph[curr]["lat"]
        lng0 = graph[curr]["lng"]
        trajectory.append({"lat": lat0, "lng": lng0})

        # check arrival
        if curr == tgt_key: # 40.777989547618326-73.95411775294352
            return {"reached": True, "final_node": curr,
                    "final_distance_to_target": 0.0, "visited": visited}
        
        # loop detection
        if len(visited) >= 2 and curr == visited[-2]:
            break

        visited.append(curr)

        node = graph[curr]
        lat, lng = node["lat"], node["lng"] # correctly lat/lng from the graph node

        # build neighbor info
        neighbors = []
        for nb_key, meta in node["links"].items():
            nb_lat, nb_lng = parse_coord(nb_key)
            dist = haversine(lat, lng, nb_lat, nb_lng)
            # relative heading from current agent heading
            nb_heading = meta["heading"]
            rel = (nb_heading - heading + 360) % 360
            neighbors.append({
                "key": nb_key,
                "abs_heading": nb_heading,
                "rel_heading": rel,
                "dist": dist,
                "text": meta.get("text", "")
            })

        # decide desired relative angle by current action
        # action = parsed_directions[dir_idx]["action"].lower()
        # if action == "left":
        #     target_rel = 270.0
        # elif action == "right":
        #     target_rel = 90.0
        # else:
        #     target_rel = 0.0
        target_rel = 0.0
        # select neighbor minimizing angular difference
        best = min(neighbors,
                   key=lambda nb: angular_diff(nb["rel_heading"], target_rel))
        
        # optionally fetch visuals and save, should be done when generating the environment, here just for debugging
        observations = []
        if args.multimodal:
            observations = fetch_streetview_images(lat, lng, args.google_api_key)
            if args.save_visuals:
                for i, img_bytes in enumerate(observations):
                    fname = f"{curr}_{i}.jpg"
                    save_path = os.path.join(args.res_folder, 'res_img', str(idx), fname)  # join base dir and filename
                    with open(save_path, "wb") as f:
                        f.write(img_bytes)

        # subtract traveled distance
        traveled = best["dist"]
        prev_rem = remaining
        remaining -= traveled

        # if crossed threshold (closest to zero), advance to next instruction
        take_action = False
        if abs(remaining) > abs(prev_rem):
            dir_idx += 1
            if dir_idx < len(parsed_directions):
                action = parsed_directions[dir_idx]["action"].lower()
                remaining = parsed_directions[dir_idx]["distance"]
                take_action = True
            else:
                print("No action to take, reached end of directions.")
                break

        # build VLM prompt and call agent
        if take_action:
            prompt_text = (
                f"Current node: {curr}\n"
                f"Target: {tgt_key}\n"
                f"Visited: {visited}\n"
                "Neighbors:\n"
            )
            if action == "left":
                action_prompt = ("At the current node, you need to turn left. That means, among the adjacent neighbor nodes, you should identify the one with the most leftward relative heading angle and move toward it.")
            elif action == "right": 
                action_prompt = ("At the current node, you need to turn right. That means, among the adjacent neighbor nodes, you should identify the one with the most rightward relative heading angle and move toward it.")
        else:
            prompt_text = (
                f"Current node: {curr}\n"
                f"Target: {tgt_key}\n"
                f"Visited: {visited}\n"
                "Neighbors:\n"
            )
            action_prompt = ("At the current node, you need to go straight. That means, among the adjacent neighbor nodes, you should identify the one with the most forward-facing relative heading angle and move toward it.")
        for nb in neighbors:
            prompt_text += (
                f"- {nb['key']} | abs_heading={nb['abs_heading']:.1f}° "
                f"rel_heading={nb['rel_heading']:.1f}° dist={nb['dist']:.1f}m\n"
            )
        if args.multimodal: # Need to revise prompt for multimodal VLM
            choice, token_usage = call_vlm_agent(
                args, observations, prompt_text, action_prompt, 
                # {nb["key"]: {"heading": nb["abs_heading"], "text": nb["text"]} for nb in neighbors},
                # tgt_key, abs(remaining)
            )
        else:
            # text-only VLM call
            choice, token_usage = call_vlm_agent(args, prompt_text=prompt_text, action_prompt=action_prompt)

        # validate and move
        if choice in graph[curr]["links"] and choice not in visited:
            curr = choice
            # update heading to the edge's absolute heading
            heading = graph[visited[-1]]["links"][choice]["heading"]
        else:
            print("invalid or revisiting node → stop")
            break

    # compute final distance to target
    flat, flng = parse_coord(curr)
    final_dist = haversine(flat, flng, tlat, tlng)
    output_dict = {
        "reached": False,
        "final_node": curr,
        "final_distance_to_target": final_dist,
        "visited": visited,
        "token_usage": token_usage
    }

    logger.info(f"Finished navigation idx={idx}: final_node={curr}, distance_to_target={final_dist:.1f}m, visited_count={len(visited)}")

    return output_dict, trajectory

if __name__ == "__main__":
    # --------------------------------------------
    # Command-line argument parsing
    # --------------------------------------------
    parser = argparse.ArgumentParser(
        description="Navigate outdoor environments using OCR and VLM"
    )
    parser.add_argument(
        "--google_api_key",
        default="",
        help="Google StreetView API key"
    )
    parser.add_argument(
        "--openai_api_key",
        default="",
        help="OpenAI API key"
    )
    parser.add_argument(
        "--gemini_api_key",
        default="",
        help="Google Gemini API key"
    )
    parser.add_argument(
        "--internvl_api_key",
        default="",
        help="InternVL API key"
    )
    parser.add_argument(
        "--dashscope_api_key",
        default="",
        help="Qwen API key"
    )
    parser.add_argument(
        "--max_steps",
        type=int,
        default=80,
        help="Maximum navigation steps before stopping"
    )
    parser.add_argument(
        "--map_screenshot_path",
        default="/home/ruis/code/embodied/tasks/navigation/data_collection/map_screenshot.jpg",
        help="Path to the OpenStreetMap screenshot for OCR"
    )
    parser.add_argument(
        "--environments_path",
        default="/home/ruis/code/embodied/tasks/navigation/data_collection/navi_env_0.json",
        help="Path to the JSON file defining navigation environments"
    )
    parser.add_argument(
        "--traj_path",
        default="/home/ruis/code/embodied/tasks/navigation/data_collection/navi_traj_0.json",
        help="Path to the trajectory JSON for computing initial heading"
    )
    parser.add_argument(
        "--res_folder",
        default="/home/ruis/code/embodied/tasks/navigation/results",
        help="Folder where to save navigation results and trajectory files"
    )
    parser.add_argument(
        "--multimodal",
        action="store_true",
        help="If set, include StreetView images in VLM prompts"
    )
    parser.add_argument(
        "--save_visuals",
        action="store_true",
        help="If set, save fetched StreetView images to disk"
    )

    # LLM and VLM Params
    parser.add_argument('--model_name', type=str, default='gpt-4o-mini-2024-07-18')  # Example: 'gpt-4o-mini', gemini-2.0-flash, 
    parser.add_argument('--max_tokens', type=int, default=300)
    parser.add_argument(
        "--temperature",     
        type=float,            
        default=1.0,         
        help="temperature"
    )
    parser.add_argument(
        "--top_p",                
        type=float,            
        default=1.0,         
        help="top_p"   
    )
    args = parser.parse_args()

    # Log hyperparameters (mask API keys)
    logger.info(f"Starting run with max_steps={args.max_steps}, multimodal={args.multimodal}, save_visuals={args.save_visuals}")
    logger.info(f"Map screenshot: {args.map_screenshot_path}")
    logger.info(f"Environments JSON: {args.environments_path}")
    logger.info(f"Trajectory JSON: {args.traj_path}")
    logger.info(f"Results folder: {args.res_folder}")

    # Configuration
    max_steps = args.max_steps  # override for this function

    # Price calculation
    if "gpt-4o-mini" in args.model_name:
        model_price = "gpt-4o-mini"  # or "gpt-4o-mini-cached"
    elif "gemini-2.0-flash" in args.model_name:
        model_price = "gemini-2.0-flash"
    elif "qwen" in args.model_name:
        model_price = "qwen-vl-plus"
    elif "internvl" in args.model_name:
        model_price = "internvl2.5-latest"

    # Model initialization
    if "gpt" in args.model_name:
        if os.getenv('OPENAI_API_KEY'):
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        else:
            client = OpenAI(api_key=args.openai_api_key)
    elif "gemini" in args.model_name:
        if os.getenv('GEMINI_API_KEY'):
            client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        else:
            client = genai.Client(api_key=args.gemini_api_key)
    elif "qwen" in args.model_name: # dashscope_api_key
        if os.getenv('DASHSCOPE_API_KEY'):
            client = OpenAI(
                api_key=os.getenv('DASHSCOPE_API_KEY'),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        else:
            client = OpenAI(
                api_key=args.dashscope_api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
    elif "internvl" in args.model_name:
        if os.getenv('INTERNVL_API_KEY'):
            client = OpenAI(
                api_key=os.getenv('INTERNVL_API_KEY'),
                base_url="https://chat.intern-ai.org.cn/api/v1/",
            )
        else:
            client = OpenAI(
                api_key=args.internvl_api_key,
                base_url="https://chat.intern-ai.org.cn/api/v1/",
            )

    # Path
    map_screenshot_path = args.map_screenshot_path # "/home/ruis/code/embodied/tasks/navigation/data_collection/map_screenshot.jpg"  # OpenStreetMap screenshot with highlighted path
    environments_path = args.environments_path # '/home/ruis/code/embodied/tasks/navigation/data_collection/navi_env/navi_env_0.json'
    res_folder = args.res_folder
    res_traj_folder = os.path.join(res_folder, 'res_traj')
    envs = load_environments(environments_path) # simply load the json file
    directions_text, ocr_usage = call_vlm_agent(args, is_ocr=True, image_path=map_screenshot_path) # Checked, OCR works well, NOTE ocr_usage should be taken into account
    parsed_directions = parse_directions(directions_text) # parse the directions text
    import pdb; pdb.set_trace()
    print("************************")
    print(parsed_directions)
    print("************************")
    initial_heading = get_initial_heading(args.traj_path) # "/home/ruis/code/embodied/tasks/navigation/data_collection/navi_traj/navi_traj_0.json" # can be a single one or a list of trajectories
    if type(envs) is not list:
        envs = [envs]

    for idx, env in enumerate(tqdm(envs,desc="Navigating Environments")):
        # import pdb; pdb.set_trace()
        logger.info(f"[Env {idx}] source={env['source']} → target={env['target']}")
        print(f"\n=== Environment {idx}: {env['source']} → {env['target']} ===")
        output_dict, trajectory = navigate_environment(args, idx, env, parsed_directions, initial_heading)
        print(f"Final node: {output_dict['final_node']}, "
              f"Distance to target: {output_dict['final_distance_to_target']:.1f}m, "
              f"Visited nodes: {len(output_dict['visited'])}, "
              f"Token Usage: {output_dict['token_usage']}")
        # Log final result and token usage
        # Calculate cost
        token_usage = output_dict.get("token_usage", {})
        if 'gpt' or 'internvl' or 'qwen' in args.model:
            prompt_tokens = token_usage.prompt_tokens
            completion_tokens = token_usage.completion_tokens
            total_cost = calculate_cost(model_price, prompt_tokens, completion_tokens)
            logger.info(f"[Env {idx}] reached={output_dict['reached']}, final_node={output_dict['final_node']}, "
                        f"final_dist={output_dict['final_distance_to_target']:.1f}m, "
                        f"visited={len(output_dict['visited'])}, "
                        f"completion_tokens={token_usage.completion_tokens}, "
                        f"prompt_tokens={token_usage.prompt_tokens}, "
                        f"total_tokens={token_usage.total_tokens}, "
                        f"total_cost={total_cost}")
        elif 'gemini' in args.model:
            candidates_token_count = token_usage.candidates_token_count
            prompt_token_count = token_usage.prompt_token_count
            total_token_count = token_usage.total_token_count
            total_cost = calculate_cost(model_price, prompt_token_count, candidates_token_count)
            logger.info(f"[Env {idx}] reached={output_dict['reached']}, final_node={output_dict['final_node']}, "
                        f"final_dist={output_dict['final_distance_to_target']:.1f}m, "
                        f"visited={len(output_dict['visited'])}, "
                        f"candidates_token_count={token_usage.candidates_token_count}, "
                        f"prompt_token_count={token_usage.prompt_token_count}, "
                        f"total_token_count={token_usage.total_token_count}, "
                        f"total_cost={total_cost}")

        # Prepare output structure
        res_traj = {"coordinates": trajectory}
        res_traj_path = f"/home/ruis/code/embodied/tasks/navigation/results/res_traj_shopping/res_traj_{idx}.json"
        with open(res_traj_path, "w") as f:
            json.dump(res_traj, f, indent=4)  # Write trajectory to JSON file
        print(f"Trajectory saved to {res_traj_path}")
        # print(f"Navigation {'SUCCESS' if success else 'FAILURE'} for environment {idx}")
        # merge json files
        merge_json(res_traj_folder, res_folder) # merge all res_traj files into one
        # add task ids
        add_task_ids(os.path.join(res_folder, "res_traj_merge_shopping.json"), os.path.join(res_folder, "res_traj_idx_merge_shopping.json"))