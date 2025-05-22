#!/usr/bin/env bash
# =============================================================================
# run_inference.sh
#
# A wrapper script to launch the unified Web+Embodied inference pipeline.
# Usage: bash run_inference.sh [OPTIONS]
# =============================================================================

### —— Configuration —— ###
NAVI_ANNO_PATH="${1:-/path/to/downloaded/data/folder/navi_anno_merge_v1_2.json}"
NAVI_ENV_PATH="${2:-/path/to/downloaded/data/folder/navi_env_merge.json}"
MAP_IMAGE_FOLDER="${3:-/path/to/downloaded/data/folder/map_screenshot}"
MAP_IMAGE_PATH="${4:-//path/to/downloaded/data/folder/map_screenshot/map_screenshot_0.jpg}"
TRAJ_PATH="${5:-/path/to/downloaded/data/folder/navi_traj/navi_traj_0.json}"
RESULT_DIR="${6:-/path/to/downloaded/data/folder/results}"
GOOGLE_API_KEY="${7:-your-google-api-key}"
OPENAI_API_KEY="${8:-your-openai-api-key}"
MODEL_NAME="${9:-gpt-4o-mini-2024-07-18}"
ACTION_TAG="${10:-id_accessibility_tree}"
OBS_TYPE="${11:-accessibility_tree}"
MAX_NAV_STEPS="${12:-80}"
MULTIMODAL_FLAG="${13:-false}"
SAVE_VISUALS_FLAG="${14:-false}"

### —— Export API keys —— ###
export GOOGLE_API_KEY
export OPENAI_API_KEY

### —— Create result directory if missing —— ###
mkdir -p "${RESULT_DIR}"

### —— Invoke Python inference —— ###
python3 /models/outdoor/inference.py \
  --navi_anno_path   "${NAVI_ANNO_PATH}" \
  --navi_env_path    "${NAVI_ENV_PATH}" \
  --map_image_folder "${MAP_IMAGE_FOLDER}" \
  --map_image_path   "${MAP_IMAGE_PATH}" \
  --traj_path        "${TRAJ_PATH}" \
  --result_dir       "${RESULT_DIR}" \
  --google_api_key   "${GOOGLE_API_KEY}" \
  --openai_api_key   "${OPENAI_API_KEY}" \
  --model_name       "${MODEL_NAME}" \
  --action_tag       "${ACTION_TAG}" \
  --obs_type         "${OBS_TYPE}" \
  --max_nav_steps    "${MAX_NAV_STEPS}" \
  $( [ "${MULTIMODAL_FLAG}" = "true" ] && echo "--multimodal" ) \
  $( [ "${SAVE_VISUALS_FLAG}" = "true" ] && echo "--save_visuals" )

echo ">>> Inference finished. Results are in ${RESULT_DIR}"