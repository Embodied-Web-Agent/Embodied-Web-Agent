import pandas as pd
from openai import OpenAI
import google.generativeai as genai
from google.generativeai import GenerativeModel
import argparse
from dotenv import load_dotenv
import os
import json
import re
import subprocess
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

from utils import *
from prompt import *

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

'''Class for standpoint nodes (intial and adjacent)'''
class StandpointNode:
    def __init__(self, id, latitude, longitude, parent=None):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.adjacent = []
        self.parent = parent
        self.visited = False
        self.num_adjacent = None
    
    def get_coords(self):
        return f'{self.latitude}, {self.longitude}'
    
    # Get all adjacent standpoints (degree=1)
    def store_adjacent(self, meta, session_token):
        links = meta.get('links', [])
        
        for link in links:
            pano_meta = get_pano_meta_from_id(link['panoId'], GOOGLE_API_KEY, session_token=session_token)

            if pano_meta is None:
                # print(f"No metadata found for adjacent standpoint.")
                continue

            longitude = pano_meta.get('lng', None)
            latitude = pano_meta.get('lat', None)
            self.adjacent.append(StandpointNode(link['panoId'], latitude, longitude, parent=self))

        self.num_adjacent = len(self.adjacent)

'''Convert model name to API style'''
def model_family_to_api_style(model):
    if model.startswith("gpt"):
        return "gpt"
    elif model.startswith("gemini"):
        return "gemini"
    elif model.startswith("qwen"):
        return "gpt"
    elif model.startswith("internvl"):
        return "gpt"
    else:
        raise ValueError(f"Unknown model: {model}")

'''Format text appropriately for the model family'''
def format_text(text, model_family='gpt'):
    # - For 'gpt': wraps text with {"type": "text", "text": text}
    # - For 'gemini': returns raw text
    if model_family == 'gemini':
        return text
    else if model_family == 'gpt':
        return [{"type": "text", "text": text}]

'''Class for the agent'''
class Agent:
    def __init__(self, client, model, model_family):
        self.client = client
        self.model = model # exact model, e.g., gpt-4o, gemini-2.0-flash, qwen-vl-plus, internvl2.5-latest
        self.model_family = model_family # model family, eg. gpt, gemini

    def generate_action(self, valid_actions, init_node_id, curr_node_id):
        prompt = GENERATE_ACTION.format(initial_id=init_node_id, current_id=curr_node_id, actions=valid_actions)
        response = self.call_vlm(prompt)
        action = self.parse(response, 'action')
        return action

    def generate_web_query(self, image_messages, web_context):
        query_history_str = "\n".join(f"{i+1}. {entry['text']}" for i, entry in enumerate(web_context))
        response = self.call_vlm(GENERATE_WEB_QUERY.format(query_history=query_history_str), context=image_messages)
        web_query = self.parse(response, 'web_query')
        return web_query

    def evaluate_confidence(self, image_messages, web_context):
        full_context = list(image_messages) 
        if web_context:
            web_context.append(format_text("Here are some relevant web search results.", model_family=self.model_family))
            full_context.extend(web_context)

        response = self.call_vlm(ESTIMATE_CONFIDENCE, context=full_context)
        confidence = self.parse(response, 'confidence')
        return confidence
    
    def generate_prediction(self, full_context):
        response = self.call_vlm(GENERATE_PREDICTION, context=full_context)
        prediction = parse_prediction(response)
        return response, prediction
    
    def call_vlm(self, prompt, max_tokens=400, temperature=0.7, context=None):
        api_style = model_family_to_api_style(self.model_family)
        if api_style == 'gpt':
            return self.call_gpt_base(prompt, self.model, max_tokens, temperature, context)
        if api_style == 'gemini':
            return self.call_gemini(prompt, self.model, max_tokens, temperature, context)
        
    def call_gpt_base(self, prompt, model, max_tokens=400, temperature=0.7, context=None):
        message_content = [{"type": "text", "text": prompt}] 
        if context:
            message_content += context 
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user", 
                    "content": message_content
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return (response.choices[0].message.content)
    
    def call_gemini(self, prompt, model, max_tokens=400, temperature=0.7, context=None):
        content = [prompt]
        if context:
            content += context
        response = self.client.generate_content(content)
        return response.text

    def parse(self, output, kind):
        if kind == 'action':
            reasoning_match = re.search(r"Reasoning Steps:\s*(.*?)(?=\nAction:)", output, re.DOTALL)
            action_match = re.search(r"^Action:\s*(.*)$", output, re.MULTILINE)

            reasoning_text = reasoning_match.group(1).strip() if reasoning_match else ""
            value = action_match.group(1).strip() if action_match else None
            return value

        elif kind == 'web_query':
            reasoning_match = re.search(r"Reasoning Steps:\s*(.*?)(?=\nIntent Template:)", output, re.DOTALL)
            intent_template_match = re.search(r"Intent Template:\s*(.*)", output)
            intent_match = re.search(r"Intent:\s*(.*)", output)
            element_match = re.search(r"Element:\s*(.*)", output)
            string_note_match = re.search(r"String Note:\s*(.*)", output)

            reasoning_text = reasoning_match.group(1).strip() if reasoning_match else ""
            intent_template = clean_brackets(intent_template_match.group(1).strip() if intent_template_match else "")
            intent = clean_brackets(intent_match.group(1).strip() if intent_match else "")
            element = clean_brackets(element_match.group(1).strip() if element_match else "")
            string_note = clean_brackets(string_note_match.group(1).strip() if string_note_match else "")
            return {
                "intent_template": intent_template,
                "intent": intent,
                "element": element,
                "string_note": string_note
            }
        
        elif kind == 'confidence':
            reasoning_match = re.search(r"Reasoning Steps:\s*(.*?)(?=\nConfidence:)", output, re.DOTALL)
            confidence_match = re.search(r"Confidence:\s*(High|Medium|Low)", output)

            reasoning_text = reasoning_match.group(1).strip() if reasoning_match else ""
            value = confidence_match.group(1).strip() if confidence_match else None
            return value


'''Add new images to a running list of image messages'''
def add_images(image_messages, coords, init_id, cache_dir_base, model_family='gpt'):
    headings = [0, 90, 180, 270]
    directions = ["north", "east", "south", "west"]
    api_style = model_family_to_api_style(model_family)

    if api_style == 'gemini':
        for deg, direction in zip(headings, directions):
            image, _ = get_street_view_from_api(
                GOOGLE_API_KEY, coords, heading=deg, size="600x400", cache_dir=cache_dir_base + f"/{init_id}/{coords}"
            )
            image_messages.append(f"This is the view facing {direction}.")
            image_messages.append(image)  # image as a PIL.Image 
    if api_style == 'gpt':
        for deg, direction in zip(headings, directions):
            image, _ = get_street_view_from_api(GOOGLE_API_KEY, coords, heading=deg, size="600x400", cache_dir=cache_dir_base + f"/{init_id}/{coords}")
            b64 = encode_image(image)
            image_messages.append({"type": "text", "text": f"This is the view facing {direction}."})
            image_messages.append({
                "type": "image_url",
                "image_url": {"url":f"data:image/jpeg;base64,{b64}"},
            })

'''Check Confidence'''
def is_confident(A, image_messages, web_context, move_history):
    confidence = A.evaluate_confidence(image_messages, web_context)
    move_history.append('Estimating Confidence: ' + str(confidence))
    # print(f'Confidence: {confidence}')

    if confidence == 'High':
        return True
    else:
        return False


'''Run the agent on the initial standpoint and adjacent nodes'''
def run(init_node, A, iter_num=5):
    image_messages = []
    web_context = []

    move_history = []
    visited = []

    adjacent_ids = [adj_node.id for adj_node in init_node.adjacent]
    init_coords = init_node.get_coords()

    # Get observations of initial standpoint
    image_messages.append(format_text("This is the initial standpoint.", model_family=A.model_family))
    add_images(image_messages, init_coords, init_node.id, f"interactive_views/{A.model_family}", model_family=A.model_family)

    # Estimate confidence given all initial observations
    if is_confident(A, image_messages, web_context, move_history):
        return image_messages, web_context, move_history, visited, True

    # If confidence is not high, allow agent to move to adjacent nodes
    curr_node = init_node
    for _ in range(iter_num):
        valid_actions = []

        # Only allow visitation to adjacent nodes we haven't seen before
        for adjacent_id in adjacent_ids:
            if adjacent_id not in visited:
                action = f"Move[{adjacent_id}]"
                valid_actions.append(action)

        if valid_actions:
            # Get action from agent (move to adjacent node or backtrack if possible)
            action = A.generate_action(valid_actions, init_node.id, curr_node.id)
            # print(f'Taking Action: {action}')

            # If not valid action, retry up to 3 times, else fail task
            if action not in valid_actions:
                # print(f"Invalid action: {action}. Retrying...")
                for attempt in range(3):
                    action = A.generate_action(valid_actions, init_node.id, curr_node.id)
                    # print(f"Retry {attempt+1}: {action}")
                    if action in valid_actions:
                        break
                else:
                    print("Task FAILED.")
                    return image_messages, web_context, move_history, visited, False
            
            move_history.append(action)

            if action.startswith("Move"):
                # Move to adjacent node
                target_id = re.search(r'Move\[(.*?)\]', action).group(1)
                target_node = next((adj_node for adj_node in init_node.adjacent if adj_node.id == target_id), None)
                visited.append(target_id)

                curr_node = target_node
                coords = curr_node.get_coords()

                image_messages.append(format_text(f"This is a standpoint adjacent the initial. ID: {target_id}", model_family=A.model_family))
                add_images(image_messages, coords, init_node.id, f"interactive_views/{A.model_family}", model_family=A.model_family)

                # Estimate confidence given all observations (including new images)
                if is_confident(A, image_messages, web_context, move_history):
                    break

                # If confidence is not high, allow agent to query Wikipedia
                # Get web search query (intent_tmemplate, element, intent, string_note)
                web_query = A.generate_web_query(image_messages, web_context)
                move_history.append(f"Querying Web: {web_query['intent']}")
                # print(f"Web Query: {web_query['intent']}")

                # Run VWA and get result
                vwa_result = run_vwa(web_query, model=A.model_family)

                web_context.append(format_text(f"{web_query['intent']}: {vwa_result}", model_family=A.model_family))
                move_history.append(f"Web Query Response: {vwa_result}")
                print(f"Web Query Answer: {vwa_result}")

                # Check confidence again
                if is_confident(A, image_messages, web_context, move_history):
                    break
        
        else:
            # No more actions available -> must generate prediction
            break
    
    return image_messages, web_context, move_history, visited, True


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='gpt')
    return parser.parse_args()


def process_row(row):
    print(f"Thread {threading.current_thread().name} is processing {row[0]}")

    args = parse_args()
    if args.model == 'gpt': #gpt-4o
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        client_model = "gpt-4o"
        api_style = "gpt"
    elif args.model == 'gemini': # gemini-2.0-flash
        # Initialize the model with generation config
        # TODO: Clean up config and move elsewhere
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        generation_config = {
            "max_output_tokens": 400,
            "temperature": 0.7,
            "top_p": 1.0
        }
        client_model = "gemini-2.0-flash"
        client = genai.GenerativeModel(model_name=client_model, generation_config=generation_config)
        api_style = "gemini"
    elif args.model == 'qwen': # qwen-vl-plus
        client = OpenAI(api_key=os.getenv("QWEN_API_KEY"), base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
        client_model = "qwen-vl-plus"
        api_style = "gpt"
    elif args.model == 'internvl': # internvl2.5-latest
        client = OpenAI(api_key=os.getenv("INTERNVL_API_KEY"), base_url="https://chat.intern-ai.org.cn/api/v1/",)
        client_model = "internvl2.5-latest"
        api_style = "gpt"

    session_token = get_session_token(GOOGLE_API_KEY)

    id, init_coords, continent, country, city, street = row
    
    # Skip already processed standpoints -- comment out to re-process standpoints
    results_path = f"interactive_views/{args.model}/{id}/result.json"
    if os.path.exists(results_path):
        print(f"Skipping {id}: result.json already exists.")
        return

    latitude, longitude = map(float, init_coords.split(","))

    curr_node = StandpointNode(id, latitude, longitude)

    meta = get_pano_meta(latitude, longitude, GOOGLE_API_KEY, session_token=session_token)

    if meta is None:
        print(f"Standpoint ID: {id} - No metadata found.")
        return
    
    curr_node.store_adjacent(meta, session_token)
    
    if curr_node.num_adjacent == 0:
        print(f"Standpoint ID: {id} - No adjacent standpoints found.")
        return

    print(f"Standpoint ID: {id}")
    # print(f'Ground Truth: {continent}, {country}, {city}, {street}\n')

    agent = Agent(client, client_model, args.model)

    image_messages, web_context, move_history, visited, success = run(curr_node, A=agent, iter_num=10)

    if not success:
        print(f"Failed to run for standpoint ID: {id}")
        return

    full_context = list(image_messages)
    if web_context:
        full_context.append(format_text("Here are some relevant web search results.", model_family=agent.model_family)) 
        full_context.extend(web_context)

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
    output_dir = f"interactive_views/{args.model}/{id}"
    with open(os.path.join(output_dir, "result.json"), "w") as f:
        json.dump(result_data, f, indent=4)


def main():
    all_initial = pd.read_excel("data_source/Breadth.xlsx").drop(['economies development status', 'Population', 'CountryGroup'], axis=1)
    sampled = all_initial.sample(n=5, random_state=1) 

    rows = list(sampled.itertuples(index=False, name=None))
    print("rows:", rows)
    with ThreadPoolExecutor(max_workers=1) as pool:
        print(f"Processing {len(rows)} rows in parallel...")
        futures = list(pool.map(process_row, rows))

if __name__ == "__main__":
    main()