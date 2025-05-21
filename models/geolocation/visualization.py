import os
import json
import streamlit as st
from PIL import Image
from utils import calculate_distance

thresholds = [1, 25, 200, 750, 2500]  # Thresholds in kilometers
threshold_names = [
    "street level (1km)",
    "city level (25km)",
    "region level (200km)",
    "country level (750km)",
    "continent level (2500km)"
]

def determine_threshold(distance):
    for i, threshold in enumerate(thresholds):
        if distance <= threshold:
            return threshold_names[i]
    return "beyond continent level"

def visualize(result_dir):
    output_path = os.path.join(result_dir, "result.json")

    if not os.path.exists(output_path):
        st.error(f"result.json not found in {result_dir}")
        return
    
    with open(output_path, "r") as f:
        result = json.load(f)

    standpoint_id = result["standpoint_id"]
    gt = result["ground_truth"]
    pred = result["gpt_output"]

    gt_lat, gt_lon = map(float, gt["coords"].split(","))
    pred_lat = float(pred["coords"]["latitude"])
    pred_lon = float(pred["coords"]["longitude"])

    distance = calculate_distance(gt_lat, gt_lon, pred_lat, pred_lon)
    distance_level = determine_threshold(distance)

    st.title(f"Standpoint {standpoint_id}")
    st.subheader("Navigation Summary")

    st.markdown(f"**Total Adjacent Standpoints:** {result['num_adjacent_standpoints']}")
    st.markdown(f"**Visited Standpoints:** {len(result['adjacent_standpoints_visited'])}")
    st.markdown("**Move History:**")
    for step in result["full_move_history"]:
        st.markdown(f"- {step}")

    st.subheader("Image Observations")
    folders = [f for f in os.listdir(result_dir) if os.path.isdir(os.path.join(result_dir, f))]
    folders.sort(key=lambda f: 0 if f == gt["coords"] else 1)

    for i, coord in enumerate(folders):
        section = "This is the Initial Standpoint" if i == 0 else f"This is a visited Adjacent Standpoint"
        st.markdown(f"**{section}**")

        coord_dir = os.path.join(result_dir, coord)
        directions = ["north", "east", "south", "west"]
        cols = st.columns(4)
        for j, dir in enumerate(directions):
            img_path = os.path.join(coord_dir, f"{dir}.jpg")
            if os.path.exists(img_path):
                cols[j].image(Image.open(img_path), caption=f"{dir.capitalize()}")

    st.subheader("Prediction Output")
    st.markdown("**Reasoning Steps:**")
    st.markdown(pred["reasoning"])
    st.markdown("**Predicted Coordinate:**")
    st.markdown(f"{pred_lat}, {pred_lon}")
    st.markdown("**Predicted Location:**")
    st.markdown(f"{pred['location']['continent']}, {pred['location']['country']}, {pred['location']['city']}, {pred['location']['street']}")
    st.markdown("**Distance from Ground Truth:**")
    st.write(f"{distance:.2f} km ({distance_level})")

    st.subheader("Ground Truth")
    st.markdown(f"**Coords:** {gt['coords']}")
    st.markdown(f"**Location:** {gt['continent']}, {gt['country']}, {gt['city']}, {gt['street']}")

if __name__=="__main__":
    st.set_page_config(layout="wide")
    result_id = st.text_input("Enter Standpoint ID", "405")

    result_dir = os.path.join("interactive_views", result_id)
    if os.path.exists(result_dir):
        visualize(result_dir)
    else:
        st.warning(f"Directory not found: {result_dir}")
