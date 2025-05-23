import pandas as pd
from openai import OpenAI
import google.generativeai as genai
from prompt import GEOGUESSER_BASELINE, GEOGUESSER_BASELINE_QWEN
import argparse
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from datasets import load_dataset

from utils import get_street_view_from_api, get_session_token, get_pano_meta, parse_prediction, encode_image

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_family', type=str, default='gpt')
    parser.add_argument('--num_samples', type=int, default=200)
    parser.add_argument('--output_dir', type=str, default='baseline_views')
    parser.add_argument('--data', type=str, default='filtered')
    return parser.parse_args()


def format_text(text, model_family='gpt'):
    if model_family == 'gemini':
        return text
    elif model_family == 'gpt' or model_family == 'qwen':
        return {"type": "text", "text": text}
    

'''Format prompt and get response'''
def call_model(client, model_family, prompt, context, max_tokens=400, temperature=0.7):
    if model_family == 'gpt' or model_family == 'qwen':
        message_content = [format_text(prompt, model_family)] + context
        message_content = [m for m in message_content if m is not None]
        response = client.chat.completions.create(
            model="gpt-4o" if model_family == 'gpt' else "qwen-vl-plus",
            messages=[{"role": "user", "content": message_content}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content

    elif model_family == 'gemini':
        content = [prompt] + context
        content = [c for c in content if c is not None]
        response = client.generate_content(content)
        return response.text

def main():
    args = parse_args()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Run ID: {run_id}")

    if args.model_family == 'gpt':
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    elif args.model_family == 'gemini':
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        generation_config = {
            "max_output_tokens": 400,
            "temperature": 0.7,
            "top_p": 1.0
        }
        client_model = "gemini-2.0-flash"
        client = genai.GenerativeModel(model_name=client_model, generation_config=generation_config)
    elif args.model_family == 'qwen': # qwen-vl-plus
        client = OpenAI(api_key=os.getenv("QWEN_API_KEY"), base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
        client_model = "qwen-vl-plus"
    else:
        raise ValueError("Unsupported model family")

    session_token = get_session_token(GOOGLE_API_KEY)

    # Only use north heading
    headings = [0]

    # Sample initial standpoints
    if args.data == 'filtered':
        dataset = load_dataset("evelynhong/embodied-web-agent-geoguessr", split="train")
        sampled = dataset.to_pandas()
    elif args.data == 'breadth':
        all_initial = pd.read_excel("data_source/Breadth.xlsx").drop(['economies development status', 'Population', 'CountryGroup', 'lat', 'lng'], axis=1)
        sampled = all_initial.sample(n=args.num_samples, random_state=1)

    for _, row in sampled.iterrows():
        id = row["ID"]
        init_coords = row["DataPoint"]
        continent = row["continent"]
        country = row["country"]
        city = row["city"]
        street = row["street"]
        
        base_dir = f"{args.output_dir}/{args.model_family}/{run_id}/{id}"
        results_path = f"{base_dir}/result.json"

        # Skip already processed standpoints -- comment out to re-process standpoints
        if os.path.exists(results_path):
            print(f"Skipping {id}: result.json already exists.")
            continue

        # Get all adjacent standpoints from the initial standpoint
        latitude, longitude = map(float, init_coords.split(","))
        meta = get_pano_meta(latitude, longitude, GOOGLE_API_KEY, session_token=session_token)

        # Check if metadata exists
        if meta is None:
            # print(f"Standpoint ID: {id} - No metadata found.")
            continue

        initial_images = []
        for deg in headings:
            image, _ = get_street_view_from_api(GOOGLE_API_KEY, init_coords, heading=deg, size="600x400", cache_dir=f"{base_dir}/{init_coords}")
            initial_images.append(image)

        # Format images
        image_messages = []
        # Only use north direction instead of all directions
        directions = ["north"]
        image_messages.append(format_text("This is the initial standpoint.", args.model_family))
        for image, direction in zip(initial_images, directions):
            b64 = encode_image(image)
            image_messages.append(format_text(f"This is the view facing {direction}.", args.model_family))
            if args.model_family == 'gpt' or args.model_family == 'qwen':
                image_messages.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
            else:
                image_messages.append(image)
        # print(len(image_messages))

        if args.model_family == 'qwen':
            prompt = GEOGUESSER_BASELINE_QWEN
        else:
            prompt = GEOGUESSER_BASELINE

        # Call the model
        ans = call_model(client, args.model_family, prompt, image_messages, max_tokens=400, temperature=0.7)
        # print(f"Standpoint ID: {id}")
        # print(f'{args.model_family}:\n{ans}')
        # print(f'Ground Truth: {continent}, {country}, {city}, {street}\n')

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

        os.makedirs(base_dir, exist_ok=True)
        with open(os.path.join(base_dir, "result.json"), "w") as f:
            json.dump(result_data, f, indent=4)


if __name__ == "__main__":
    main()
