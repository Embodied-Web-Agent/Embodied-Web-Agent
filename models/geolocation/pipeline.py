from dotenv import load_dotenv
import os
import re

from utils import get_street_view_from_api, encode_image
from agent import Agent, model_family_to_api_style, format_text, is_confident, do_web_query

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

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


'''Run the pipeline where the agent doesn't have to make an initial web query'''
def run_optional(base_dir, init_node, A, iter_num=5):
    image_messages = []
    web_context = []

    move_history = []
    visited = []

    adjacent_ids = [adj_node.id for adj_node in init_node.adjacent]
    init_coords = init_node.get_coords()

    # Get observations of initial standpoint
    image_messages.append(format_text("This is the initial standpoint.", model_family=A.model_family))
    add_images(image_messages, init_coords, init_node.id, base_dir, model_family=A.model_family)

    # Estimate confidence given all initial observations
    if is_confident(A, image_messages, web_context, move_history):
        return image_messages, web_context, move_history, visited, True

    # Web interaction on initial observations
    do_web_query(A, image_messages, web_context, move_history)

    # Estimate confidence after web interaction
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
                add_images(image_messages, coords, init_node.id, base_dir, model_family=A.model_family)

                # Estimate confidence given all observations (including new images)
                if is_confident(A, image_messages, web_context, move_history):
                    break

                # If confidence is not high, allow agent to query Wikipedia
                do_web_query(A, image_messages, web_context, move_history)

                # Check confidence again
                if is_confident(A, image_messages, web_context, move_history):
                    break
        
        else:
            # No more actions available -> must generate prediction
            break
    
    return image_messages, web_context, move_history, visited, True


'''Agent is required to make a web query after initial observations'''
def run_forced(base_dir, init_node, A, iter_num=5):
    image_messages = []
    web_context = []

    move_history = []
    visited = []

    adjacent_ids = [adj_node.id for adj_node in init_node.adjacent]
    init_coords = init_node.get_coords()

    # Get observations of initial standpoint
    image_messages.append(format_text("This is the initial standpoint.", model_family=A.model_family))
    add_images(image_messages, init_coords, init_node.id, base_dir, model_family=A.model_family)

    # Estimate confidence given all initial observations
    is_confident(A, image_messages, web_context, move_history)

    # Web interaction on initial observations
    do_web_query(A, image_messages, web_context, move_history)

    # Estimate confidence after web interaction
    if is_confident(A, image_messages, web_context, move_history):
        return image_messages, web_context, move_history, visited, True

    # Allow agent to move to adjacent nodes
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
                # Move to adjacent node and add new observations to running image context
                target_id = re.search(r'Move\[(.*?)\]', action).group(1)
                target_node = next((adj_node for adj_node in init_node.adjacent if adj_node.id == target_id), None)
                visited.append(target_id)

                curr_node = target_node
                coords = curr_node.get_coords()

                image_messages.append(format_text(f"This is a standpoint adjacent the initial. ID: {target_id}", model_family=A.model_family))
                add_images(image_messages, coords, init_node.id, base_dir, model_family=A.model_family)

                # Estimate confidence given all observations (including new images)
                if is_confident(A, image_messages, web_context, move_history):
                    break

                # If confidence is not high, allow agent to query Wikipedia
                do_web_query(A, image_messages, web_context, move_history)

                # Check confidence again
                if is_confident(A, image_messages, web_context, move_history):
                    break
        
        else:
            # No more actions available -> must generate prediction
            break
    
    return image_messages, web_context, move_history, visited, True