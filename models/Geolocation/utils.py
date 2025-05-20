import requests
import os
from PIL import Image
from io import BytesIO
import math
import re
import base64
import json
import uuid
import subprocess

def get_street_view_from_api(api_key:str, location:str, heading=0, pitch=0, fov=90, size="600x400", cache_dir=None):
    """
    Get a Google Street View image for a given location and orientation.
    
    Parameters:
        api_key (str): Your Google Cloud API key.
        location (str): The location as "latitude,longitude" (e.g., "37.4219999,-122.0840575").
        heading (int): The compass heading of the camera (0-360 degrees).
        pitch (int): The up or down angle of the camera (from -90 to 90).
        fov (int): The field of view of the image (from 0 to 120).
        size (str): The size of the image in pixels, as "widthxheight" (e.g., "600x400").
    
    Returns:
        Image object if successful, None otherwise.
        True/False if the image is cached.
    """

    # create cache directory if it doesn't exist togethet with all its parent directories
    if cache_dir is not None:
        os.makedirs(cache_dir, exist_ok=True)
        heading_to_dir = {0: "north", 90: "east", 180: "south", 270: "west"}
        cache_id = f"{heading_to_dir[heading]}.jpg"
        cache_path = os.path.join(cache_dir, cache_id)
        if os.path.exists(cache_path):
            return Image.open(cache_path), True
    
    base_url = "https://maps.googleapis.com/maps/api/streetview"
    params = {
        "size": size,
        "location": location,
        "heading": heading,
        "pitch": pitch,
        "fov": fov,
        "key": api_key
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        # Load image from response content
        image = Image.open(BytesIO(response.content))
        if cache_dir is not None:
            image.save(cache_path)
        return image, False
    else:
        print("Error fetching Street View image:", response.status_code, response.text)
        return None, False
    
def get_session_token(api_key:str):
    url = "https://tile.googleapis.com/v1/createSession"
    headers = {"Content-Type": "application/json"}
    payload = {
        "mapType": "streetview",
        "language": "en-US",
        "region": "US"
    }
    response = requests.post(f"{url}?key={api_key}", json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["session"]
    else:
        print("Error fetching session token:", response.status_code, response.text)
        return None
    
def get_pano_meta(latitute, longitude, api_key:str, session_token:str, radius:float=50):
    url = "https://tile.googleapis.com/v1/streetview/metadata"
    response = requests.get(f"{url}?session={session_token}&key={api_key}&lat={latitute}&lng={longitude}&radius={radius}")
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching panorama metadata:", response.status_code, response.text)
        return None

def get_pano_meta_from_id(pano_id, api_key:str, session_token:str):
    url = "https://tile.googleapis.com/v1/streetview/metadata"
    response = requests.get(f"{url}?session={session_token}&key={api_key}&panoId={pano_id}")
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching panorama metadata from meta ID:", response.status_code, response.text)
        return None
    
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth's surface
    using the haversine formula.

    Args:
        lat1 (float): Latitude of the first point in decimal degrees.
        lon1 (float): Longitude of the first point in decimal degrees.
        lat2 (float): Latitude of the second point in decimal degrees.
        lon2 (float): Longitude of the second point in decimal degrees.

    Returns:
        float: Distance between the two points in kilometers.
    """
    try:
        R = 6371.0  # Earth's radius in kilometers
        lat1_rad = math.radians(float(lat1))
        lon1_rad = math.radians(float(lon1))
        lat2_rad = math.radians(float(lat2))
        lon2_rad = math.radians(float(lon2))

        delta_lat = lat2_rad - lat1_rad
        delta_lon = lon2_rad - lon1_rad

        a = math.sin(delta_lat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c

    except:
        print("Parsing Error!")
        distance = float('inf')

    return distance

"""Parse the model output"""
def parse_prediction(output):
    reasoning = ""
    parsed_coords = ""
    parsed_location = ""

    reasoning_match = re.search(r"Reasoning Steps:\s*(.*?)(?=\nEstimated Coordinate:)", output, re.DOTALL)
    coord_match = re.search(r"Estimated Coordinate:\s*([-\d.]+,\s*[-\d.]+)", output)
    location_match = re.search(r"Estimated Location:\s*(.*)", output)

    if reasoning_match:
        reasoning = reasoning_match.group(1).strip()

    if coord_match:
        parsed_coords = coord_match.group(1).replace(" ", "") 

    if location_match:
        parsed_location = location_match.group(1).strip()

    parsed_coords = parsed_coords.split(",")
    out_latitude = parsed_coords[0].strip() if parsed_coords else ""
    out_longitude = parsed_coords[1].strip() if len(parsed_coords) > 1 else ""

    parsed_location = parsed_location.split(",")
    out_continent = parsed_location[0].strip() if parsed_location else ""
    out_country = parsed_location[1].strip() if len(parsed_location) > 1 else ""
    out_city = parsed_location[2].strip() if len(parsed_location) > 2 else ""
    out_street = parsed_location[3].strip() if len(parsed_location) > 3 else ""

    return {
        "reasoning": reasoning,
        "latitude": out_latitude,
        "longitude": out_longitude,
        "continent": out_continent,
        "country": out_country,
        "city": out_city,
        "street": out_street
    }

'''Encode image to base64'''
def encode_image(image):
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

'''Run VisualWebArena for web search'''
def run_vwa(web_query):
    vwa_task = [
        {
            "sites": ["wikipedia"],
            "task_id": 0,
            "require_login": True,
            "storage_state": "./.auth/wikipedia_state.json",
            "start_url": "__WIKIPEDIA__",
            "geolocation": None,
            "intent_template": web_query["intent_template"],
            "intent": web_query["intent"],
            "image": None,
            "instantiation_dict": {"element": web_query["element"]},
            "require_reset": False,
            "viewport_size": { "width": 1280 },
            "eval": {
                "eval_types": ["string_match"],
                "reference_answers": { "fuzzy_match": ["N/A"] },
                "string_note": web_query["string_note"],
            },
            "intent_template_id": 0,
            "reasoning_difficulty": "easy",
            "visual_difficulty": "easy",
            "comments": "",
            "overall_difficulty": "easy"
        }
    ]

    visualwebarena_dir = os.path.abspath("../../../visualwebarena")
    raw_path = os.path.join(visualwebarena_dir, "config_files/vwa/geo_task.raw.json")
    output_dir = f"output/geo_query_{uuid.uuid4().hex[:8]}"
    output_path = os.path.join(visualwebarena_dir, output_dir)

    # Save the raw.json config file for vwa execution
    with open(raw_path, "w") as f:
        json.dump(vwa_task, f, indent=2)

    env = os.environ.copy()
    env["PYTHONPATH"] = visualwebarena_dir

    # Generate json config file: python ../../../visualwebarena/scripts/generate_test_data.py
    subprocess.run(
        ["python", "scripts/generate_test_data.py"],
        cwd=visualwebarena_dir,
        env=env
    )

    # Run web search task in vwa: 
    subprocess.run([
        "python", "run.py",
        "--instruction_path", "agent/prompts/jsons/p_som_cot_id_actree_3s.json",
        "--test_start_idx", "0",
        "--test_end_idx", "1",
        "--result_dir", output_dir,
        "--test_config_base_dir", "config_files/vwa/geo_task",
        "--model", "gpt-4o",
        "--action_set_tag", "som",
        "--observation_type", "image_som"
    ], cwd=visualwebarena_dir, env=env)

    # Get web search results and parse
    html_path = os.path.join(output_path, "render_0.html")
    vwa_result = extract_parsed_answer_from_html(html_path)
    return vwa_result

'''Get vwa answer from html doc'''
def extract_parsed_answer_from_html(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Extract the final answer inside 'parsed_action'
    match = re.search(
        r"<div class='parsed_action'[^>]*?><pre>stop \[(.*?)\]</pre>", html, re.DOTALL
    )

    if not match:
        raise ValueError("Could not find parsed_action answer in HTML.")

    answer = match.group(1).strip()
    return answer


def clean_brackets(text):
    return text.strip().strip("<>").strip()