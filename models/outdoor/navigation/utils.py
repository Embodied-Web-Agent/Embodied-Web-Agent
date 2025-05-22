import requests
import os
import json
import math
import re
import heapq
from pathlib import Path
from PIL import Image
from io import BytesIO

import osmnx as ox
from shapely.geometry import Point
from shapely.ops import nearest_points

def get_heading_diff(head1, head2):
    return min(abs(head1 - head2), abs(head1 - head2 + 360), abs(head1 - head2 - 360))

def get_street_view_from_api(api_key:str, location:str, heading=0, pitch=0, fov=90, size="600x400", cache_dir="navigation/data/street_views"):
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
    os.makedirs(cache_dir, exist_ok=True)

    cache_id = f"{location}_{heading}_{pitch}_{fov}_{size}.jpg"
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
        image.save(cache_path)
        return image, False
    else:
        print("Error fetching Street View image:", response.status_code, response.text)
        return None, False

def get_nearest_road_from_api(api_key, latitude, longitude):
    """
    Finds the nearest point on the road to the given coordinates.
    
    Parameters:
        api_key (str): Your Google Cloud API key.
        latitude (float): The latitude of the building.
        longitude (float): The longitude of the building.
    
    Returns:
        tuple: A tuple of (latitude, longitude) for the nearest point on the street,
               or None if the request fails.
    """
    base_url = "https://roads.googleapis.com/v1/snapToRoads"
    params = {
        "path": f"{latitude},{longitude}",
        "interpolate": "false",
        "key": api_key
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        # Parse the response to get snapped location
        data = response.json()
        if "snappedPoints" in data and data["snappedPoints"]:
            snapped_point = data["snappedPoints"][0]["location"]
            return snapped_point["latitude"], snapped_point["longitude"]
        else:
            print("No snapped points found.")
            return None
    else:
        print("Error fetching nearest road:", response.status_code, response.text)
        return None

def get_closest_street_location(G, latitude, longitude):
    u, v, key = ox.distance.nearest_edges(G, X=longitude, Y=latitude)

    # Extract the coordinates of the endpoints of the nearest edge
    edge_data = G[u][v][key]
    nearest_road = edge_data["geometry"]
    print("Nearest road segment coordinates:", list(nearest_road.coords))

    # Create a line segment (edge) from the two endpoints
    # edge_line = LineString([point1, point2])

    # Create a point from the target coordinate
    target_point = Point(longitude, latitude)

    # Find the nearest point on the edge line to the target point
    projected_point = nearest_points(target_point, nearest_road)[1]
    projected_latitude = projected_point.y
    projected_longitude = projected_point.x
    return projected_latitude, projected_longitude

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

def get_pano_id(meta):
    # The panoID in meta is transient, we need to get a immortal id calculated by lat and lon
    return str(meta["lat"]) + str(meta["lng"])

def get_meta_distance(meta_a, meta_b):
    return ox.distance.great_circle_vec(meta_a["lat"], meta_a["lng"], meta_b["lat"], meta_b["lng"])

def get_panograph_around_location(latitute, longitude, api_key:str, distance_threshold:float=50.0):
    session_token = get_session_token(api_key)
    if session_token is None:
        return None

    meta = get_pano_meta(latitute, longitude, api_key, session_token)
    if meta is None:
        return None
    
    if "links" not in meta:
        
        latitute, longitude = get_nearest_road_from_api(api_key, latitute, longitude)
        meta = get_pano_meta(latitute, longitude, api_key, session_token)
        if meta is None:
            return None
    
    # Constructing a graph of panoramas with metadata using breadth-first search
    source_node_id = get_pano_id(meta)
    pano_graph = {
        source_node_id: {
            "google_pano_id": meta["panoId"],
            "lat": meta["lat"],
            "lng": meta["lng"],
            "links": {},
        }
    }
    visited = set()
    queue = [meta]

    while queue:
        current_meta = queue.pop(0)
        current_id = get_pano_id(current_meta)
        if current_id in visited:
            continue

        visited.add(current_id)

        if "links" not in current_meta:
            print(current_meta)
            continue

        for link in current_meta["links"]:
            pano_meta = get_pano_meta_from_id(link['panoId'], api_key, session_token)

            if pano_meta is None:
                continue

            if get_meta_distance(meta, pano_meta) > distance_threshold:
                continue

            pano_id = get_pano_id(pano_meta)

            if pano_id not in pano_graph[current_id]["links"]:
                pano_graph[current_id]["links"][pano_id] = {
                    "google_pano_id": pano_meta["panoId"],
                    "heading": link["heading"],
                    "text": link["text"],
                    "elevaionAboveEgm96": link["elevationAboveEgm96"]
                }

            if pano_id not in pano_graph:
                queue.append(pano_meta)
                pano_graph[pano_id] = {
                    "google_pano_id": pano_meta["panoId"],
                    "lat": pano_meta["lat"],
                    "lng": pano_meta["lng"],
                    "links": {},
                }

    return pano_graph

###### Outdoor Navigation ######

# Pricing per 1 million tokens (USD)
MODEL_PRICING = { # to be updated
    "gpt-4o-mini": {
        "prompt": 0.15, # input
        "completion": 0.60 # output
    },
    "gemini-2.0-flash": {
        "prompt": 0.10, # input
        "completion": 0.40 # output
    },
    "qwen-vl-plus": { # https://www.alibabacloud.com/help/zh/model-studio/models#5540e6e52e1xx
        "prompt": 0.21, # input
        "completion": 0.63 # output
    },
    "internvl2.5-latest": { # to be confirmed
        "prompt": 0, # input
        "completion": 0 # output
    }
}

def calculate_cost(model_name, prompt_tokens, completion_tokens):
    if model_name not in MODEL_PRICING:
        raise ValueError(f"Unknown model '{model_name}'")

    pricing = MODEL_PRICING[model_name]
    cost_prompt = (prompt_tokens / 1_000_000) * pricing["prompt"]
    cost_completion = (completion_tokens / 1_000_000) * pricing["completion"]
    total_cost = round(cost_prompt + cost_completion, 6)

    return total_cost

def load_environments(path):
    """Load navigation environments from JSON file."""
    with open(path, "r") as f:
        return json.load(f)

def compute_heading(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the initial bearing (heading) from point A to point B.

    Parameters:
        lat1 (float): Latitude of point A in degrees.
        lon1 (float): Longitude of point A in degrees.
        lat2 (float): Latitude of point B in degrees.
        lon2 (float): Longitude of point B in degrees.
    
    lat1, lon1 = 40.77803317678347, -73.95422161115864
    lat2, lon2 = 40.777989547618326, -73.95411775294352
    heading = compute_heading(lat1, lon1, lat2, lon2)

    Returns:
        float: Heading in degrees clockwise from true north, in the range [0, 360).
    """
    # Convert degrees to radians
    phi1 = math.radians(lat1)
    lambda1 = math.radians(lon1)
    phi2 = math.radians(lat2)
    lambda2 = math.radians(lon2)

    # Compute difference in longitude
    delta_lambda = lambda2 - lambda1

    # Compute components for the bearing formula
    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    # Calculate the bearing using atan2, result is in radians
    theta = math.atan2(x, y)

    # Convert radians to degrees and normalize to [0, 360)
    bearing = (math.degrees(theta) + 360) % 360
    return bearing

def get_initial_heading(trajectory_path: str) -> float:
    """
    Load a trajectory JSON file containing a 'coordinates' list,
    read the first two points and compute the initial heading.
    """
    with open(trajectory_path, "r") as f:
        data = json.load(f)
    coords = data.get("coordinates", [])
    if len(coords) < 2:
        raise ValueError("Trajectory must contain at least two points.")
    lat1, lon1 = coords[0]["lat"], coords[0]["lng"]
    lat2, lon2 = coords[1]["lat"], coords[1]["lng"]
    return compute_heading(lat1, lon1, lat2, lon2)

def add_task_ids(infile: str | Path, outfile: str | Path) -> None:
    """
    Read a JSON file containing a list of dicts, add a sequential
    'task_id' to each element (starting at 0), and write the result
    to a new JSON file.

    Parameters
    ----------
    infile : str | Path
        Path to the input JSON file.
    outfile : str | Path
        Path where the augmented list will be saved.
    """
    # --- read ---------------------------------------------------------------
    with open(infile, "r", encoding="utf-8") as f:
        data: list[dict] = json.load(f)

    # --- modify -------------------------------------------------------------
    for idx, element in enumerate(data):
        element["task_id"] = idx              # add sequential id

    # --- write --------------------------------------------------------------
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points (in meters)."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def angular_diff(a: float, b: float) -> float:
    """
    Compute the minimal difference between two angles (in degrees).
    """
    return abs((a - b + 180) % 360 - 180)

# Dijkstra algorithm to compute the shortest path between start and target nodes in the graph.
def dijkstra_shortest_path(graph, start, target):
    # distances: store the minimum distance to each node; initialize start node distance to 0
    distances = {node: math.inf for node in graph}
    distances[start] = 0

    # predecessor: to reconstruct the shortest path
    predecessors = {}

    # priority queue (min-heap): stores tuples of (distance, node_key)
    queue = [(0, start)]

    while queue:
        current_distance, current_node = heapq.heappop(queue)

        # If the current node is the target, we can stop early
        if current_node == target:
            break

        # If we found a longer distance in the queue than the best known, skip it
        if current_distance > distances[current_node]:
            continue

        # Iterate over all neighbors of the current node
        # The neighbors are found in the "links" dictionary for the current node
        for neighbor in graph[current_node]["links"]:
            # Get the geographic coordinates for the current node and the neighbor
            curr_lat = graph[current_node]["lat"]
            curr_lng = graph[current_node]["lng"]
            # Ensure neighbor exists in the graph
            if neighbor not in graph:
                continue
            neighbor_lat = graph[neighbor]["lat"]
            neighbor_lng = graph[neighbor]["lng"]

            # Compute the distance between the current node and the neighbor
            weight = haversine(curr_lat, curr_lng, neighbor_lat, neighbor_lng)
            distance_through_current = current_distance + weight

            # If a shorter path to the neighbor is found, update its distance and predecessor
            if distance_through_current < distances[neighbor]:
                distances[neighbor] = distance_through_current
                predecessors[neighbor] = current_node
                heapq.heappush(queue, (distance_through_current, neighbor))

    # If the target is unreachable, return None
    if distances[target] == math.inf:
        return None

    # Reconstruct the path by following predecessors from target to start
    path = []
    node = target
    while node != start:
        path.append(node)
        node = predecessors[node]
    path.append(start)
    path.reverse()  # reverse the path to get it from start to target
    return path

def read_json_file(file_path):
    """
    Reads a JSON file from the given file path and returns the loaded JSON data.
    
    Args:
        file_path (str): The path to the JSON file.
        
    Returns:
        dict: The JSON data loaded into a Python dictionary.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data

def merge_json(folder_path, data_folder):
    """
    In the given folder_path, this function finds all JSON files with names
    matching the pattern "navi_env_<number>.json". It then loads the contents of each
    file into a list, where the index corresponds to the number in the filename.
    Finally, the merged list is saved as a new JSON file named "merged.json" in the folder.
    """
    if "navi_anno" in folder_path:
        # List all JSON files in the folder that match the naming pattern
        json_files = [f for f in os.listdir(folder_path)
                    if f.startswith("navi_anno_") and f.endswith(".json")]
        # Function to extract the numeric index from the filename
        def extract_index(filename):
            m = re.search(r'navi_anno_(\d+)\.json$', filename)
            return int(m.group(1)) if m else -1
    elif "navi_env" in folder_path:
        # List all JSON files in the folder that match the naming pattern
        json_files = [f for f in os.listdir(folder_path)
                    if f.startswith("navi_env_") and f.endswith(".json")]
        # Function to extract the numeric index from the filename
        def extract_index(filename):
            m = re.search(r'navi_env_(\d+)\.json$', filename)
            return int(m.group(1)) if m else -1
    elif "navi_traj" in folder_path:
        # List all JSON files in the folder that match the naming pattern
        json_files = [f for f in os.listdir(folder_path)
                    if f.startswith("navi_traj_") and f.endswith(".json")]
        # Function to extract the numeric index from the filename
        def extract_index(filename):
            m = re.search(r'navi_traj_(\d+)\.json$', filename)
            return int(m.group(1)) if m else -1
    elif "res_traj" in folder_path:
        # List all JSON files in the folder that match the naming pattern
        json_files = [f for f in os.listdir(folder_path)
                    if f.startswith("res_traj_") and f.endswith(".json")]
        # Function to extract the numeric index from the filename
        def extract_index(filename):
            m = re.search(r'res_traj_(\d+)\.json$', filename)
            return int(m.group(1)) if m else -1
    else:
        print("Unsupported folder path for merging JSON files.")  

    # Extract indices from all files and determine the maximum index
    indices = [extract_index(f) for f in json_files if extract_index(f) != -1]
    if not indices:
        print("No JSON files found with the expected naming pattern.")
        return

    max_index = max(indices)
    # Initialize a list with length max_index + 1
    merged_list = [None] * (max_index + 1)

    # Read each JSON file and store its content at the corresponding index
    for filename in json_files:
        idx = extract_index(filename)
        if idx == -1:
            continue
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        merged_list[idx] = content

    # Save the merged list as a new JSON file named "merged.json"
    if "navi_anno" in folder_path:
        merged_file_path = os.path.join(data_folder, "navi_anno_merge.json")
    elif "navi_env" in folder_path:
        merged_file_path = os.path.join(data_folder, "navi_env_merge.json")
    elif "navi_traj" in folder_path:
        merged_file_path = os.path.join(data_folder, "navi_traj_merge.json")
    elif "res_traj" in folder_path:
        merged_file_path = os.path.join(data_folder, "res_traj_merge.json")
    else:
        print("Unsupported folder path for merging JSON files.")
    with open(merged_file_path, 'w', encoding='utf-8') as f:
        json.dump(merged_list, f, ensure_ascii=False, indent=4)

    print(f"Merged JSON file saved at: {merged_file_path}")