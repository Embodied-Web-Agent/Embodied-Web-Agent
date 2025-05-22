#!/bin/bash
# This script runs the outdoor_navigation.py with specified command line parameters.

python models/outdoor/navigation/outdoor_navigation.py \
  --model_name gpt-4o-mini-2024-07-18 \
  --max_tokens 300 \
  --temperature 1.0 \
  --max_steps 100 \
  --map_screenshot_path /path/to/map_screenshot/map_screenshot_x.png \
  --environments_path /path/to/navigation/data_collection/shopping_env_x.json \
  --traj_path /path/to/navigation/data_collection/shopping_traj_x.json