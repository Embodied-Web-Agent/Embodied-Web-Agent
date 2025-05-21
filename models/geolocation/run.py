import pandas as pd
from openai import OpenAI
import google.generativeai as genai
from google.generativeai import GenerativeModel
import argparse
from dotenv import load_dotenv
import os
import json
import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import uuid
from datetime import datetime
from functools import partial

from utils import get_session_token, get_pano_meta
from standpoint import StandpointNode
from agent import Agent, format_text
from pipeline import run_optional, run_forced


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_family', type=str, default='gpt')
    parser.add_argument('--num_samples', type=int, default=200)
    parser.add_argument('--output_dir', type=str, default='interactive_views')
    parser.add_argument('--run_forced', type=bool, default=True)
    return parser.parse_args()


def process_row(row, run_id):
    # print(f"Process {multiprocessing.current_process().name} is processing {row[0]}")

    args = parse_args()

    if args.model_family == 'gpt':
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        client_model = "gpt-4o"
        api_style = "gpt"

    elif args.model_family == 'gemini':
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        generation_config = {
            "max_output_tokens": 400,
            "temperature": 0.7,
            "top_p": 1.0
        }
        client_model = "gemini-2.0-flash"
        client = genai.GenerativeModel(model_name=client_model, generation_config=generation_config)
        api_style = args.model_family

    elif args.model_family == 'qwen': # qwen-vl-plus
        client = OpenAI(api_key=os.getenv("QWEN_API_KEY"), base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
        client_model = "qwen-vl-plus"
        api_style = "gpt"

    elif args.model_family == 'internvl': # internvl2.5-latest
        client = OpenAI(api_key=os.getenv("INTERNVL_API_KEY"), base_url="https://chat.intern-ai.org.cn/api/v1/",)
        client_model = "internvl2.5-latest"
        api_style = "gpt"

    else:
        raise ValueError(f"Unsupported model family: {args.model_family}")

    session_token = get_session_token(GOOGLE_API_KEY)

    id, init_coords, continent, country, city, street = row

    base_dir = f"{args.output_dir}/{args.model_family}/{run_id}"
    
    # Skip already processed standpoints -- comment out to re-process standpoints
    results_path = f"{base_dir}/{id}/result.json"
    if os.path.exists(results_path):
        print(f"Skipping {id}: result.json already exists.")
        return

    latitude, longitude = map(float, init_coords.split(","))

    # Create the initial standpoint node
    curr_node = StandpointNode(id, latitude, longitude)

    # Get metadata for the initial standpoint
    meta = get_pano_meta(latitude, longitude, GOOGLE_API_KEY, session_token=session_token)

    if meta is None:
        # print(f"Standpoint ID: {id} - No metadata found.")
        return
    
    # Store the initial standpoint's adjacent nodes (if any)
    curr_node.store_adjacent(meta, session_token)
    
    # Skip if no adjacent nodes are found
    if curr_node.num_adjacent == 0:
        # print(f"Standpoint ID: {id} - No adjacent standpoints found.")
        return

    print(f"Standpoint ID: {id}")
    # print(f'Ground Truth: {continent}, {country}, {city}, {street}\n')

    # Create the agent
    agent = Agent(client, client_model, args.model_family)

    # Run the pipeline
    if args.run_forced:
        image_messages, web_context, move_history, visited, success = run_forced(base_dir, curr_node, A=agent, iter_num=5)
    else:
        image_messages, web_context, move_history, visited, success = run_optional(base_dir, curr_node, A=agent, iter_num=5)

    # Don't store results if the run fails
    if not success:
        print(f"Failed to run for standpoint ID: {id}")
        return

    # Prepare images + web context for prediction
    full_context = list(image_messages)
    if web_context:
        full_context.append(format_text("Here are some relevant web search results.", model_family=agent.model_family)) 
        full_context.extend(web_context)
        # print(f"Web context: {web_context}")

    # Generate the prediction using the entire context
    ans, parsed = agent.generate_prediction(full_context)

    # print(f'Predicted Location: {parsed["continent"]}, {parsed["country"]}, {parsed["city"]}, {parsed["street"]}')

    result_data = {
        "standpoint_id": id,
        "ground_truth": {
            "coords": init_coords,
            "continent": continent,
            "country": country,
            "city": city,
            "street": street
        },
        "full_move_history": move_history,
        "adjacent_standpoints_visited": visited,
        "gpt_output": {
            "full_output": ans,
            "reasoning": parsed["reasoning"],
            "coords": {
                "latitude": parsed["latitude"],
                "longitude": parsed["longitude"]
            },
            "location": {
                "continent": parsed["continent"],
                "country": parsed["country"],
                "city": parsed["city"],
                "street": parsed["street"]
            }
        },
        "num_adjacent_standpoints": curr_node.num_adjacent,
    }

    output_dir = f"{base_dir}/{id}"
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "result.json"), "w") as f:
        json.dump(result_data, f, indent=4)


def main():
    args = parse_args()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Run ID: {run_id}")

    all_initial = pd.read_excel("data_source/Breadth.xlsx").drop(['economies development status', 'Population', 'CountryGroup', 'lat', 'lng'], axis=1)
    sampled = all_initial.sample(n=args.num_samples, random_state=1) 

    rows = list(sampled.itertuples(index=False, name=None))

    # with ProcessPoolExecutor(max_workers=5) as pool:
    #     process_func = partial(process_row, run_id=run_id)
    #     print(f"Processing {len(rows)} rows in parallel...")
    #     futures = list(pool.map(process_func, rows))

    futures = []
    for row in rows:
        result = process_row(row, run_id)
        futures.append(result)


if __name__ == "__main__":
    main()