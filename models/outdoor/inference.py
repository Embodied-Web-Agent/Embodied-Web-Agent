import os
import sys
import argparse
import json
import tempfile
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Add project root to PYTHONPATH for imports
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent  # adjust if needed
sys.path.insert(0, str(PROJECT_ROOT))

# Import web interaction functions
from web_interaction import (
    config as web_config,
    prepare as web_prepare,
    dump_config as web_dump_config,
    get_unfinished as web_get_unfinished,
    test as web_test,
)

# Import navigation functions
from navigation.outdoor_navigation import (
    load_environments,
    ocr_map_directions_vlm,
    parse_directions,
    get_initial_heading,
    navigate_environment,
)


def run_web_subtask_full(
    web_cfg: Dict[str, Any], args: argparse.Namespace
) -> None:
    """
    Execute a web subtask by writing the full config JSON and invoking the web interaction pipeline.
    """
    # Create temporary directory for this subtask
    temp_dir = tempfile.mkdtemp()
    cfg_path = Path(temp_dir) / "subtask.json"
    # Write the full config as expected by web_interaction
    with open(cfg_path, 'w', encoding='utf-8') as f:
        json.dump(web_cfg, f, indent=2)

    # Prepare arguments for web_interaction
    w_args = web_config()
    w_args.test_config_base_dir = str(temp_dir)
    w_args.result_dir = args.result_dir
    # propagate LLM parameters if needed
    w_args.model = args.model_name
    w_args.action_set_tag = args.action_tag
    w_args.observation_type = args.obs_type
    w_args.render = False
    w_args.render_screenshot = True
    w_args.save_trace_enabled = False
    w_args.sleep_after_execution = 1.0
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # Run preparation and execution
    web_prepare(w_args)
    web_dump_config(w_args)
    # Identify configs to run
    to_run = web_get_unfinished([str(cfg_path)], args.result_dir)
    if to_run:
        web_test(w_args, to_run)
    # Cleanup
    shutil.rmtree(temp_dir)
    logger.info(f"Completed web subtask: {web_cfg.get('task_id')}")


def main():
    # Parse CLI arguments
    parser = argparse.ArgumentParser(
        description="Unified pipeline for web + embodied tasks"
    )
    parser.add_argument('--navi_anno_path', required=True)
    parser.add_argument('--navi_env_path', required=True)
    parser.add_argument('--traj_path', required=True)
    parser.add_argument('--result_dir', required=True)
    parser.add_argument('--google_api_key', required=True)
    parser.add_argument('--openai_api_key', required=True)
    parser.add_argument('--model_name', default='gpt-4o-mini-2024-07-18')
    parser.add_argument('--action_tag', default='id_accessibility_tree')
    parser.add_argument('--obs_type', default='accessibility_tree')
    parser.add_argument('--max_nav_steps', type=int, default=80)
    parser.add_argument('--multimodal', action='store_true')
    parser.add_argument('--save_visuals', action='store_true')
    args = parser.parse_args()

    # Log parameters
    logger.info("Inference parameters:")
    for k, v in vars(args).items():
        logger.info(f"  {k}: {v}")

    # Set environment variables for API keys
    os.environ['GOOGLE_API_KEY'] = args.google_api_key
    os.environ['OPENAI_API_KEY'] = args.openai_api_key

    # Load task annotations and environments
    tasks = json.load(open(args.navi_anno_path, 'r', encoding='utf-8'))
    envs = load_environments(args.navi_env_path)
    if not isinstance(envs, list):
        envs = [envs]

    # Iterate over tasks
    for idx, task in enumerate(tqdm(tasks, desc="Running Tasks")):
        general = task['general']
        task_id = general['task_id']
        logger.info(f"Starting task {task_id} of type {general['task_type']}")

        # Merge web and embodied subtasks and sort by sub_task_id
        subtasks = task.get('web', []) + task.get('embodied', [])
        subtasks_sorted = sorted(subtasks, key=lambda s: s['sub_task_id'])

        # Prepare initial values
        directions_text = None
        initial_heading = None

        # For each subtask
        for sub in subtasks_sorted:
            sub_id = sub['sub_task_id']
            stype = sub['subtask_type']
            composite_id = f"{task_id}_{sub_id}"
            logger.info(f"Running subtask {composite_id}: {stype}")

            if stype == 'web':
                # Transform to full web config
                web_cfg = {
                    **sub,
                    'task_id': composite_id
                }
                # Run web subtask
                run_web_subtask_full(web_cfg, args)

                # If intent includes route, extract OCR directions
                if 'route' in sub['intent'].lower():
                    # find latest screenshot and run OCR VLM
                    from embodied.tasks.navigation.outdoor_navigation import ocr_map_directions_vlm
                    directions_text = ocr_map_directions_vlm(
                        os.path.join(args.result_dir, 'screenshot.png')
                    )

            elif stype == 'embodied':
                # Ensure we have directions for navigation
                if directions_text is None:
                    raise RuntimeError("Missing directions_text for embodied subtask")
                # Compute initial heading once
                if initial_heading is None:
                    initial_heading = get_initial_heading(args.traj_path)

                # Parse directions and navigate
                steps = parse_directions(directions_text)
                output, traj = navigate_environment(
                    args, idx, envs[idx], steps, initial_heading
                )
                # Save trajectory
                out_path = Path(args.result_dir) / f"traj_{composite_id}.json"
                with open(out_path, 'w') as f:
                    json.dump({'coordinates': traj}, f, indent=2)
                logger.info(f"Saved trajectory to {out_path}")

            else:
                logger.warning(f"Unknown subtask type: {stype}")

        logger.info(f"Completed task {task_id}")

if __name__ == '__main__':
    main()
