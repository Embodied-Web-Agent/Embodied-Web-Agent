# Select a standpoint -> 
# call google street view API to get the adjacent points -> 
# call google street view API to get the image observation of standpoint and adjacent points -> 
# prompt geoguessr instructions and all image observation of the standpoint and adjacent points to the VLM -> 
# VLM output the continent, country, and city name of the standpoint -> 
# Evaluate correct or not?

import pandas as pd
from openai import OpenAI
from utils import get_street_view_from_api, get_session_token, get_pano_meta, get_pano_meta_from_id, parse_prediction, encode_image
from prompt import *
import argparse
from dotenv import load_dotenv
import os
import base64
import json
import re

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

'''Format gpt prompt and get response'''
def call_gpt(client, system_message, image_messages, max_tokens=400, temperature=0.5):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user", 
                "content": [{"type": "text", "text": system_message}] + image_messages
            }
        ],
        max_tokens=max_tokens,
        temperature=temperature
    )
    return (response.choices[0].message.content)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='gpt')
    return parser.parse_args()

def main():
    args = parse_args()
    if args.model == 'gpt':
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    elif args.model == 'qwen':
        client = OpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"), base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    session_token = get_session_token(GOOGLE_API_KEY)

    # Only use north heading
    headings = [0] #, 90, 180, 270]

    # Sample initial standpoints
    all_initial = pd.read_excel("data_source/Breadth.xlsx").drop(['economies development status', 'Population', 'CountryGroup'], axis=1)
    sampled = all_initial.sample(n=200, random_state=1)

    for _, row in sampled.iterrows():
        id, init_coords, continent, country, city, street = row

        # Skip already processed standpoints -- comment out to re-process standpoints
        results_path = f"baseline_views/{id}/result.json"
        if os.path.exists(results_path):
            print(f"Skipping {id}: result.json already exists.")
            continue

        # Get all adjacent standpoints from the initial standpoint
        latitude, longitude = map(float, init_coords.split(","))
        meta = get_pano_meta(latitude, longitude, GOOGLE_API_KEY, session_token=session_token)

        # Check if metadata exists
        if meta is None:
            print(f"Standpoint ID: {id} - No metadata found.")
            continue
        
        # Skip getting adjacent standpoints
        # adjacent_standpoints = []
        # links = meta.get('links', [])
        # for link in links:
        #     print(link)
        #     pano_meta = get_pano_meta_from_id(link['panoId'], GOOGLE_API_KEY, session_token=session_token)
        #     # Check if adjacent metadata exists
        #     if pano_meta is None:
        #         print(f"No metadata found for adjacent standpoint.")
        #         continue
        #     adjacent_standpoints.append(pano_meta)

        # Get images for all four cardinal directions
        all_images = []
        initial_images = []
        for deg in headings:
            image, _ = get_street_view_from_api(GOOGLE_API_KEY, init_coords, heading=deg, size="600x400", cache_dir=f"baseline_views/{id}/{init_coords}")
            initial_images.append(image)
        all_images.append(initial_images)

        # Format images
        image_messages = []
        # Only use north direction instead of all directions
        directions = ["north"] #, "east", "south", "west"]
        for i, image_list in enumerate(all_images):
            image_messages.append({"type": "text", "text": f"This is the initial standpoint."})
            # No need to concat the adjacent image standpoints 
            # else:
            #     image_messages.append({"type": "text", "text": f"This is a standpoint adjacent to the initial."})
            for image, direction in zip(image_list, directions):
                b64 = encode_image(image)
                image_messages.append({"type": "text", "text": f"This is the view facing {direction}."})
                image_messages.append({
                    "type": "image_url",
                    "image_url": {"url":f"data:image/jpeg;base64,{b64}"},
                })
        print(len(image_messages))
        # Call the model
        ans = call_gpt(client, GEOGUESSER_BASELINE, image_messages, max_tokens=400, temperature=0.7)
        print(f"Standpoint ID: {id}")
        print("Number of adjacent standpoints:", 0)
        print(f'GPT:\n{ans}')
        print(f'Ground Truth: {continent}, {country}, {city}, {street}\n')

        parsed = parse_prediction(ans)

        result_data = {
            "standpoint_id": id,
            "ground_truth": {
                "coords": init_coords,
                "continent": continent,
                "country": country,
                "city": city,
                "street": street
            },
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
            "num_adjacent_standpoints": 0,
        }
        output_dir = f"baseline_views/{id}"
        with open(os.path.join(output_dir, "result.json"), "w") as f:
            json.dump(result_data, f, indent=4)


if __name__ == "__main__":
    main()
