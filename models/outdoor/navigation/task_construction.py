import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import osmnx as ox
import json
from tasks.navigation.utils import get_panograph_around_location
import argparse

def get_closest_node_from_graph_json(graph_json, target_location):
    target_lat, target_lon = target_location
    closest_node = None
    closest_distance = float("inf")
    for node_id, node_meta in graph_json.items():
        node_lat, node_lon = node_meta["lat"], node_meta["lng"]
        distance = ox.distance.great_circle_vec(node_lat, node_lon, target_lat, target_lon)
        if distance < closest_distance:
            closest_distance = distance
            closest_node = node_id
    return closest_node

def construct_surrounding_graph_from_paronama(
    source_location = (34.0694767, -118.4443319), # Engneering VI
    target_location = (34.0703956, -118.4442832), # Ackerman Union
    coefficient=1.0,
):
    API_KEY = os.getenv("GOOGLE_API_KEY")
    source_lat, source_lon = source_location
    target_lat, target_lon = target_location
    distance = ox.distance.great_circle_vec(source_lat, source_lon, target_lat, target_lon)
    print(f"Distance between source and target is {distance} meters")
    return get_panograph_around_location(source_lat, source_lon, API_KEY, distance_threshold=distance * coefficient)

def construct_navi_task(
    source_location = (34.0694767, -118.4443319), # Engneering VI
    target_location = (34.0703956, -118.4442832), # Ackerman Union
    dump_path = "navigation/data/navi_task.json",
    coefficient = 1.0,
):
    # sample a subgraph from G based on the source and target locations
    pano_graph_json = construct_surrounding_graph_from_paronama(source_location, target_location, coefficient)

    source_node_id = get_closest_node_from_graph_json(pano_graph_json, source_location)
    target_node_id = get_closest_node_from_graph_json(pano_graph_json, target_location)

    task_json = {
        "source": source_node_id,
        "target": target_node_id,
        "graph": pano_graph_json
    }
    
    # get the base dir of dump path
    base_dir = os.path.dirname(dump_path)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    with open(dump_path, "w") as f:
        json.dump(task_json, f, indent=4)
    
    print(f"Navigation task has been successfully saved to {dump_path}")

def parse_coordinates(value):
    """
    Parse a string in the format '(lat, lon)' or 'lat,lon' into a tuple (lat, lon).
    """
    try:
        # Remove parentheses if they exist
        value = value.strip("()")
        lat, lon = map(float, value.split(","))
        return lat, lon
    except ValueError:
        raise argparse.ArgumentTypeError("Coordinates must be in the format '(lat, lon)' or 'lat,lon'.")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source_location', type=parse_coordinates, default=(34.0694767, -118.4443319)) # Engneering VI
    parser.add_argument('--target_location', type=parse_coordinates, default=(34.0703956, -118.4442832)) # Ackerman Union
    parser.add_argument('--coefficient', type=str, default='1.0')
    parser.add_argument('--dump_path', type=str, default='tasks/navigation/data/navi_task.json')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    dump_path = args.dump_path
    source_location = args.source_location
    target_location = args.target_location
    coefficient = float(args.coefficient)
    construct_navi_task(source_location, target_location, dump_path, coefficient)
