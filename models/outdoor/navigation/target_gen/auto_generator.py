"""
Code to navigate outdoor environments using OCR and VLM.
"""

import math
import random
import json
from pathlib import Path
import os
import logging
import datetime
import math
import heapq
import argparse
import sys
import re
from tqdm import tqdm
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.outdoor.navigation.utils import get_pano_meta, get_session_token, get_pano_meta_from_id, calculate_cost, add_task_ids, read_json_file, merge_json, haversine, dijkstra_shortest_path
from models.outdoor.navigation.task_construction import construct_navi_task # construct the env
from models.outdoor.navigation.target_gen.generator import DataGenerator # generate the endpoints

from models.outdoor.navigation.target_gen.llm import ChatBot, OpenAIChatBot
from models.outdoor.navigation.data_collection.prompt.web_task_gen_rui import SUB_TASK_GEN_PROMPT, SUB_TASK_SYSTEM_PROMPT, SUB_TASK_GEN_PROMPT_V2, SUB_TASK_SYSTEM_PROMPT_V2

# Updated parse_coordinate function to correctly handle the negative sign for longitude.
# The coordinate string is assumed to be in the format "<latitude>-<longitude>".
# For locations in NYC, the longitude should be negative.
def parse_coordinate(coord_str):
    # If the coordinate string starts with '-', then the latitude is negative.
    # Find the index of the separator hyphen that separates latitude and longitude.
    if coord_str[0] == '-':
        # Skip the minus sign for latitude and find the next hyphen.
        sep_index = coord_str.find('-', 1)
    else:
        sep_index = coord_str.find('-')
    if sep_index == -1:
        raise ValueError("Invalid coordinate format: " + coord_str)
    
    # Parse latitude from the start up to the separator.
    lat = float(coord_str[:sep_index])
    # Parse longitude from after the separator.
    # Since the intended longitude is negative (as in NYC), we explicitly add the negative sign.
    lng = -float(coord_str[sep_index+1:])
    return lat, lng

# This function takes an input distance (in meters), the graph (as a dictionary),
# and the source coordinate (as a string). It randomly selects and returns a node (by its key)
# from the graph whose distance from the source is greater than the given distance.
def get_random_node_above_distance(distance_threshold, graph, source):
    # Parse the source coordinate string into latitude and longitude.
    source_lat, source_lng = parse_coordinate(source)

    # Initialize a list to hold nodes that are beyond the threshold distance.
    valid_nodes = []
    max_distance: float = -1.0       # Track the largest distance seen so far.
    farthest_node: str | None = None # Node corresponding to max_distance.

    # Iterate through all nodes in the graph.
    for node in graph:
        if node == source:           # Skip the source itself.
            continue
        # Parse the node coordinate from the node key.
        node_lat, node_lng = parse_coordinate(node)
        # Calculate the distance from the source to the current node.
        d = haversine(source_lat, source_lng, node_lat, node_lng)
        # Check if the distance is greater than the threshold and skip the source itself.
        if d > distance_threshold:
            valid_nodes.append(node)

        # Update farthest node found so far.
        if d > max_distance:
            max_distance = d
            farthest_node = node

    # If no nodes are found that satisfy the condition, print the error message.
    if not valid_nodes: # Potential Problem: if no node, there will be an error in the following lines.
        print("Distance is too large, please try a smaller distance.")
        return farthest_node # revise the potential problem above
    else:
        # Randomly select one node from the valid nodes.
        start_point = random.choice(valid_nodes)
        return start_point

# Function to format the path as required and save as JSON
def save_path_as_json(path, graph, output_file):
    # Build the coordinates list from the path nodes
    coordinates = []
    for node_key in path:
        # Each node in the graph has "lat" and "lng" keys
        coordinates.append({
            "lat": graph[node_key]["lat"],
            "lng": graph[node_key]["lng"]
        })
    result = {"coordinates": coordinates}
    # Create the directory for the output file if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    # Write the resulting JSON to the specified output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

# ---------------- Conversion Functions ----------------
# This part converts the generated items into the target JSON format.
def parse_tasks(text):
    """
    Parse the input text to extract embodied_task_intents and web_task_intents.
    This function returns a dictionary with two keys: 'embodied' and 'web',
    each containing a list of tasks. Each task is a dictionary with a sub_task_id
    and an intent field (among other default fields).
    """
    # Define regex patterns for embodied_task_intent and web_task_intent.
    embodied_pattern = re.compile(r"embodied_task_intent_(\d+):\s*(.+?)(?=\n|$)")
    web_pattern = re.compile(r"web_task_intent_(\d+):\s*(.+?)(?=\n|$)")

    # Find all matches from the input text.
    embodied_matches = embodied_pattern.findall(text)
    web_matches = web_pattern.findall(text)

    # Initialize the result dictionary with default structure.
    result = {
        "embodied": [],
        "web": []
    }

    # Process each embodied_task_intent match.
    for match in embodied_matches:
        # match[0] is the sub-task id, match[1] is the intent string.
        sub_task_id = int(match[0])
        intent_text = match[1].strip()
        embodied_task = {
            "sub_task_id": sub_task_id,
            "intent_template": "",
            "instantiation_dict": {},
            "start": "",
            "end": "",
            "intermediate": "",
            "intent": intent_text,
            "intent_template_id": "",
            "eval": {
                "eval_types": ["success_rate"],
                "reference_answer_raw_annotation": "trajectory",
                "reference_answers": "trajectory"
            },
            "subtask_type": "embodied"
        }
        result["embodied"].append(embodied_task)

    # Process each web_task_intent match.
    for match in web_matches:
        sub_task_id = int(match[0])
        intent_text = match[1].strip()
        web_task = {
            "sub_task_id": sub_task_id,
            "sites": [""],
            "require_login": False,
            "storage_state": "",
            "start_url": "http://98.80.38.242:3000/directions#map=7/41.652/-73.246&layers=Y",
            "geolocation": "",
            "intent_template": "",
            "instantiation_dict": {},
            "intent": intent_text,
            "require_reset": False,
            "viewport_size": {"width": 1280},
            "intent_template_id": "",
            "eval": {
                "eval_types": [
                    "url_match"
                ],
                "reference_answers": None,
                "reference_answer_raw_annotation": None,
                "reference_url": "",
                "program_html": [],
                "url_note": "EXACT"
            },
            "subtask_type": "web"
        }
        result["web"].append(web_task)

    return result

def convert_coordinate(coord):
    """
    Convert a coordinate list to a string format "(lat, lon)".
    """
    if not coord or len(coord) != 2:
        return ""
    lat, lon = coord
    return f"({lat}, {lon})"

def convert_item(args, endpoint, startpoint, task_id):
    """
    Convert one item from the original JSON format to the target JSON format.
    The coordinate is converted to a string and assigned to endpoint_coordinate.
    Other fields are moved to the 'general' section, and task_id is set based on the index.
    For task_type, 'navigation' 'traveling' 'shopping' 'geoguessr'
    """
    # Construct the 'embodied' part with default values
    embodied = [
        {
            "sub_task_id": 0,
            "intent_template": "",
            "instantiation_dict": {},
            "start": "",
            "end": "",
            "intermediate": "",
            "intent": "",
            "intent_template_id": "",
            "eval": {
                "eval_types": ["success_rate"],
                "reference_answer_raw_annotation": "trajectory",
                "reference_answers": "trajectory"
            },
            "subtask_type": "embodied"
        }
    ]

    # Construct the 'general' part, mapping fields from the original item
    general = {
        "annotation_status": "N/A",
        "annotator": "rui",
        "comments": "",
        "difficulty": {
            "overall_difficulty": "",
            "reasoning_difficulty": "",
            "visual_difficulty": ""
        },
        "endpoint_coordinate": convert_coordinate(endpoint.get("coordinate", "N/A")),
        "startpoint_coordinate": convert_coordinate(startpoint),  # Use the startpoint passed to the function
        "generated_instruction": endpoint.get("generated_instruction", ""),
        "generated_name": endpoint.get("generated_name", ""),
        "geocode_name": endpoint.get("geocode_name", ""),
        "geocode_types": endpoint.get("geocode_types", []),
        "task_id": task_id,
        "task_type": args.task_type # navigation, traveling, shopping, geoguessr
    }

    # Construct the 'web' part with fixed default values
    web = [
        {
            "sub_task_id": 0,
            "sites": ["map"],
            "require_login": False,
            "storage_state": "",
            "start_url": "http://98.80.38.242:3000/directions#map=7/41.652/-73.246&layers=Y",
            "geolocation": convert_coordinate(startpoint),
            "intent_template": "",
            "instantiation_dict": {},
            "intent": "",
            "require_reset": False,
            "viewport_size": {"width": 1280},
            "intent_template_id": "",
            "eval": {
                "eval_types": [
                    "url_match"
                ],
                "reference_answers": None,
                "reference_answer_raw_annotation": None,
                "reference_url": "",
                "program_html": [],
                "url_note": "EXACT"
            },
            "subtask_type": "web"
        }
    ]

    # Combine all parts into one output item
    output_item = {
        "general": general,
        "embodied": embodied,
        "web": web
    }
    return output_item

def convert_item_with_tasks(args, anno_item, tasks_text):
    """
    Convert the original JSON item and update its embodied and web sections with the tasks parsed from tasks_text.
    This function first calls convert_item to build the basic JSON structure and then parses tasks_text
    using parse_tasks. The parsed tasks replace the default embodied and web lists.
    """
    # Parse the tasks from tasks_text.
    parsed_tasks = parse_tasks(tasks_text)
    
    # Update the embodied part with the parsed embodied tasks if available.
    if parsed_tasks.get("embodied"):
        anno_item["embodied"] = parsed_tasks["embodied"]
    
    # Update the web part with the parsed web tasks if available.
    if parsed_tasks.get("web"):
        anno_item["web"] = parsed_tasks["web"]
    
    return anno_item

def convert_json(args, input_file, output_file):
    """
    Read the input JSON file, convert each item to the target format,
    and write the output JSON file.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        data = [data]
    
    output_data = []
    for idx, item in enumerate(data):
        converted_item = convert_item(args, item, idx)
        output_data.append(converted_item)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)

def auto_generate(args, task_id, logger):
    while True:
        while True: # iteratively search for a feasible endpoint until we find one with links.
            # Step 1: Generate endpoints from GPT Prompting
            generator = DataGenerator(args.prompt_load_path) # prompt file, gpt-4o-mini-2024-07-18 = gpt-4o-mini
            # endpoint = generator.generate_data('./tasks/navigation/target_gen/workspace/spot_test_data_4o_single_must_nyc_mini_rui_temp.json') # save file, not dump, filepath here no use
            endpoint, token_usage = generator.generate_data() # save file, not dump, filepath here no use
            # endpoint = read_json_file('./tasks/navigation/target_gen/workspace/spot_test_data_4o_single_must_nyc_mini_rui_temp.json')
            endpoint_lat, endpoint_lng = endpoint['coordinate'][0], endpoint['coordinate'][1]

            logger.info("Endpoint started generation")
            logger.info("Potential Results: %s", endpoint)
            logger.info("Token usage: %s", token_usage)

            # Step 2: Randomly Select one adjacent node of endpoint
            pano_meta = get_pano_meta(endpoint_lat, endpoint_lng, API_KEY, session_token)
            links = pano_meta.get("links", [])
            if len(links) != 0:
                break
        # Randomly select one dictionary from the list.
        random_point = random.choice(links)
        # Extract the 'panoId' from the selected dictionary.
        pano_id = random_point['panoId']

        pano_meta_from_id = get_pano_meta_from_id(pano_id, API_KEY, session_token)
        lat, lng = pano_meta_from_id['lat'], pano_meta_from_id['lng']

        # Step 3: Construct the navigation task JSON file from (endpoint_lat, endpoint_lng) to (lat, lng)
        source_location = (endpoint_lat, endpoint_lng)
        target_location = (lat, lng)
        navi_dump_folder = args.navi_dump_folder # tasks/navigation/data_collection/navi_env
        navi_dump_path = os.path.join(navi_dump_folder, f"navi_env_{task_id}.json")
        coefficient = float(args.coefficient)
        try:
            # Attempt to construct the navigation task.
            # This may raise an exception if the construction fails.
            construct_navi_task(source_location, target_location, navi_dump_path, coefficient)
            break
        except Exception as e:
            print(f"Error during task construction: {e}")
            print("Retrying with a different endpoint...")

    # Step 4: Randomly Choose the Start Point from the graph
    # Open and read the JSON file containing the graph.
    with open(navi_dump_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract the 'graph' data and the source coordinate from the JSON data.
    graph_data = data["graph"]
    source_coord = data["source"]

    # Define a distance threshold in meters (for example, 30 meters).
    distance_input = float(args.threshold)

    # Get a random node that is farther than the specified distance from the source.
    result = get_random_node_above_distance(distance_input, graph_data, source_coord)

    # If a valid node is found, print the result (the parsed coordinate tuple).
    if result:
        print("start_point:", parse_coordinate(result))

        # Remove the parentheses and split the string by comma
        # Strip removes leading/trailing parentheses, then split by comma to get the two parts.
        coordinate_tuple = parse_coordinate(result)

    # Specify the output JSON file path for the shortest path
    traj_dump_folder = args.traj_dump_folder # tasks/navigation/data_collection/navi_traj
    traj_dump_path = os.path.join(traj_dump_folder, f"navi_traj_{task_id}.json")

    # Extract the graph, source, and target from the input data.
    # Note: According to the problem, the coordinate in the key is (here, lat is the first part, lng is the second).
    # Unpack the tuple into latitude and longitude
    lat, lng = coordinate_tuple
    startpoint = [lat, lng]

    # Format the tuple into a string using a dash as a separator.
    # Use the absolute value of longitude to avoid a double negative.
    coordinate_string = f"{lat}-{abs(lng)}"
    start = coordinate_string # new start point
    target = source_coord

    data["source"] = start
    data["target"] = target

    # Write the updated data back to the JSON file
    with open(navi_dump_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # Step 5: Find the shortest path using Dijkstra's algorithm

    # Find the shortest path using Dijkstra's algorithm.
    shortest_path = dijkstra_shortest_path(graph_data, start, target)
    if shortest_path is None:
        print("No path found from start to target.")
    else:
        # Save the shortest path to a JSON file in the required format.
        save_path_as_json(shortest_path, graph_data, traj_dump_path)
        print("Shortest path has been saved to", traj_dump_path)

    # Step 6: Append saved path and navi into the annotation json file based on the task_id
    # Load the existing annotation JSON file
    navi_env = read_json_file(navi_dump_path) # environment file
    navi_traj = read_json_file(traj_dump_path) # trajectory file

    return navi_env, navi_traj, endpoint, startpoint

def log_experiment(response, token_usage):
    """
    Log experimental parameters and results.
    
    Parameters:
    - params: A dictionary containing experiment parameters.
    - response: GPT response data.
    - token_usage: Token usage information from the GPT response.
    """
    logger.info("Experiment started")
    # logger.info("Parameters: %s", params)
    logger.info("Results: %s", response)
    logger.info("Token usage: %s", token_usage)
    logger.info("Experiment ended")

def parse_args():
    parser = argparse.ArgumentParser()
    # parser.add_argument('--source_location', type=parse_coordinates, default=(34.0694767, -118.4443319))
    # params for navigation task generation
    parser.add_argument('--threshold', type=str, default='10')
    parser.add_argument('--coefficient', type=str, default='5.0')
    # parser.add_argument('--task_id', type=str, default='6')
    parser.add_argument('--num_sample', type=int, default=5) # Number of samples to generate.
    parser.add_argument('--start_id', type=int, default=0) # Start ID for the task generation.
    parser.add_argument('--task_type', type=str, default='navigation', choices=['navigation', 'traveling', 'shopping'])
    # params for folder and file paths
    parser.add_argument('--data_folder', type=str, default='outdoor/navigation/data_collection')
    parser.add_argument('--navi_dump_folder', type=str, default='outdoor/navigation/data_collection/navi_env')
    parser.add_argument('--traj_dump_folder', type=str, default='outdoor/navigation/data_collection/navi_traj')
    parser.add_argument('--prompt_load_path', type=str, default='outdoor/navigation/data_collection/prompt/spot_and_question_gen_rui.json')
    # parser.add_argument('--navi_all_path', type=str, default='outdoor/navigation/data/navi_task_all.json') # combine all together
    parser.add_argument('--anno_dump_folder', type=str, default='outdoor/navigation/data_collection/navi_anno')
    parser.add_argument('--logger_dump_folder', type=str, default='outdoor/navigation/data_collection/logger')
    # params for LLM
    # temp, model, and other LLM parameters can be added here if needed.
    # Note: The API key is expected to be set as an environment variable.
    # parser.add_argument('--llm_model', type=str, default='gpt-4o-mini-2024-07-18')  # Example: 'gpt-4o-mini'
    parser.add_argument('--model_name', type=str, default='gpt-4o-mini-2024-07-18')  # Example: 'gpt-4o-mini'
    parser.add_argument('--max_tokens', type=int, default=500)
    parser.add_argument(
        "--temperature",                
        type=float,            
        default=1.0,         
        help="temperature"   
    )
    return parser.parse_args()

# --- Script to read the graph from a JSON file and test the function ---
# The JSON file is assumed to be located at the specified path.
# Main script
if __name__ == "__main__":
    args = parse_args()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_name = "experiment"
    logger_name = f"{experiment_name}_{timestamp}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # Set logging level to DEBUG    
    log_filename = os.path.join(args.logger_dump_folder, f"{logger_name}.log")
    os.makedirs(args.logger_dump_folder, exist_ok=True)

    file_handler = logging.FileHandler(log_filename) # logger folder can also be anno folder
    file_handler.setLevel(logging.DEBUG)  # Set file handler logging level to DEBUG
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)  # Associate the formatter with the file handler
    logger.addHandler(file_handler)

    logger.info("Experiment parameters: %s", vars(args))

    API_KEY = os.getenv("GOOGLE_API_KEY")
    session_token = get_session_token(API_KEY)
    # init LLM chatbot
    chatbot = OpenAIChatBot(id='sub_task_gen', model=args.model_name, max_tokens=args.max_tokens, temperature=args.temperature) # o3-mini, o1-mini, gpt-4o-mini

    num_sample = args.num_sample
    start_id = args.start_id
    print(f"Generating {num_sample} samples starting from task_id {start_id}...")
    # batch generation
    for i in tqdm(range(start_id, start_id + num_sample), desc="Generating samples", unit="sample"):
        print(f"Generating sample {i+1}/{start_id + num_sample + 1}...")
        logger.info(f"Generating sample {i+1}/{start_id + num_sample + 1}...")
        # Call the auto_generate function to create a new navigation task.
        # This will generate a new start point and path each time.
        task_id = i
        navi_env, navi_traj, endpoint, startpoint = auto_generate(args, task_id, logger)
        anno_item = convert_item(args, endpoint, startpoint, task_id) # convert the endpoint and startpoint into the annotation format, single json file
        task_category = anno_item['general']['task_type'] # right now, it is the args.task_type
        generated_instruction = endpoint.get("generated_instruction", "")
        generated_name = endpoint.get("generated_name", "")

        sub_task_gen_prompt = SUB_TASK_GEN_PROMPT_V2.replace("[task_category_placeholder]", task_category)
        sub_task_gen_prompt = sub_task_gen_prompt.replace("[generated_instruction_placeholder]", generated_instruction)
        sub_task_gen_prompt = sub_task_gen_prompt.replace("[generated_name_placeholder]", generated_name)
        chatbot.load_prompt_and_instruction_sub_task_gen(SUB_TASK_SYSTEM_PROMPT_V2, sub_task_gen_prompt)
        while True:
            try:
                sub_task_gen, token_usage = chatbot.send()
                anno_item_with_tasks = convert_item_with_tasks(args, anno_item, sub_task_gen)
                break
            except Exception as e:
                print(f"Error during sub-task generation: {e}")
                continue
        log_experiment(sub_task_gen, token_usage)
        if "gpt-4o-mini" in args.model_name:
            model = "gpt-4o-mini"  # or "gpt-4o-mini-cached"
        prompt_tokens = token_usage.prompt_tokens
        completion_tokens = token_usage.completion_tokens
        total_cost = calculate_cost(model, prompt_tokens, completion_tokens)
        logger.info(f"completion_tokens={token_usage.completion_tokens}, "
                    f"prompt_tokens={token_usage.prompt_tokens}, "
                    f"total_tokens={token_usage.total_tokens}, "
                    f"total_cost={total_cost}")
        # navi_env_all = read_json_file(args.navi_all_path) # tentatively separate the json files
        anno_dump_path = os.path.join(args.anno_dump_folder, f"navi_anno_{task_id}.json")
        anno_dir = os.path.dirname(anno_dump_path)
        if not os.path.exists(anno_dir): # Check if the directory exists
            os.makedirs(anno_dir, exist_ok=True)
        with open(anno_dump_path, 'w', encoding='utf-8') as f:
            json.dump(anno_item_with_tasks, f, ensure_ascii=False, indent=4)

    # merge json function, for backend processing
    data_folder = args.data_folder
    merge_json(args.navi_dump_folder, data_folder)  # Merge navigation environment JSON files.
    merge_json(args.traj_dump_folder, data_folder)   # Merge navigation trajectory JSON files.
    merge_json(args.anno_dump_folder, data_folder)    # Merge annotation JSON files.

    # for visualization, revise the traj file, add task_id
    add_task_ids(os.path.join(data_folder, "navi_traj_merge.json"), os.path.join(data_folder, "navi_traj_idx_merge.json"))