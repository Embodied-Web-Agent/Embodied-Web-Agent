import os
import json
from pathlib import Path
import difflib
import shutil

def get_final_step_from_config(file_name, config_folder):
    """
    Get the final step from the corresponding config file
    
    Args:
        file_name (str): Name of the file being processed
        config_folder (str): Path to the config_files folder
    
    Returns:
        str: Final step text or None if not found
    """
    # Extract prefix before the first dot
    prefix = file_name.split('.')[0]
    config_file_path = os.path.join(config_folder, f"{prefix}.json")
    
    try:
        with open(config_file_path, 'r') as f:
            config_data = json.load(f)
        
        # Get RecipeWithStateChanges
        recipe_changes = config_data.get('RecipewithStateChanges', [])
        if recipe_changes:
            # Get the last element's step
            return recipe_changes[-1].get('step', None)
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    
    return None

def extract_environment_from_action(action):
    """
    Extract the environment name from a switch_environment action
    
    Args:
        action (str): Action string like "switch_environment [xxx]"
    
    Returns:
        str: Environment name or None if not a switch_environment action
    """
    if isinstance(action, str) and 'switch_environment' in action:
        # Extract content between square brackets
        start = action.find('[')
        end = action.find(']')
        if start != -1 and end != -1:
            return action[start+1:end]
    return None

def is_text_95_percent_similar(text1, text2):
    """
    Check if two texts are at least 95% similar
    
    Args:
        text1, text2 (str): Texts to compare
    
    Returns:
        bool: True if similarity is >= 0.95
    """
    if not text1 or not text2:
        return False
    
    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
    return similarity >= 0.95

def check_json_file(json_data, file_name, config_folder):
    """
    Check if a JSON file meets any of the conditions for setting finished=True
    
    Returns:
        bool: True if any condition is met, False otherwise
    """
    if 'actions' not in json_data or 'observations' not in json_data:
        return False
    
    actions = json_data['actions']
    observations = json_data['observations']
    
    # Check condition 1: 99+ actions
    if len(actions) >= 99:
        return True
    
    # Check condition 2: switch_environment in action str for 5 consecutive times
    consecutive_switch = 0
    
    for action in actions:
        if isinstance(action, str):
            # Check for switch_environment
            if 'switch_environment' in action:
                consecutive_switch += 1
                if consecutive_switch >= 5:
                    return True
            else:
                consecutive_switch = 0
        elif isinstance(action, dict):
            # Check condition 3: action is a dictionary with specific answer
            if action.get('answer') == "Early stop: Same embodied action for 10 times":
                return True
            consecutive_switch = 0
        else:
            consecutive_switch = 0
    
    # Check condition 4: disabled Next button in observations
    for observation in observations:
        if isinstance(observation, str) and "button 'Next' disabled: True" in observation:
            return True
    
    # Check condition 5: last switch_environment action is 95% similar to final step
    for action in actions:
        last_action = action
        environment = extract_environment_from_action(last_action)
        if environment:
            final_step = get_final_step_from_config(file_name, config_folder)
            if final_step and is_text_95_percent_similar(environment, final_step):
                return True
    
    return False

def process_folder(folder_path, config_folder):
    """
    Iterate through a folder and process JSON files
    
    Args:
        folder_path (str): Path to the folder to process
        config_folder (str): Path to the config_files folder
    """
    folder = Path(folder_path)
    unfinished_files = []
    
    # Create backup folder if it doesn't exist
    backup_folder = folder.parent / (folder.name + "_bkp")
    backup_folder.mkdir(exist_ok=True)
    
    for file_path in folder.iterdir():
        # Check if file has 'json' in its name
        if 'json' in file_path.name and file_path.is_file():
            try:
                # Load JSON file
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Check if any condition is met
                is_finished = check_json_file(data, file_path.name, config_folder)
                
                if not is_finished:
                    unfinished_files.append(file_path.name)
                    
                    # Handle corresponding render HTML file
                    prefix = file_path.name.split('.')[0]
                    render_file_name = f"render_{prefix}.html"
                    render_file_path = folder / render_file_name
                    
                    if render_file_path.exists():
                        # Move to backup folder
                        backup_dest = backup_folder / render_file_name
                        shutil.move(str(render_file_path), str(backup_dest))
                        print(f"Moved {render_file_name} to backup folder")
                
                print(f"Processed {file_path.name}: finished={is_finished}")
                
            except json.JSONDecodeError:
                print(f"Error: {file_path.name} is not a valid JSON file")
            except Exception as e:
                print(f"Error processing {file_path.name}: {str(e)}")
    
    # Write unfinished files to check_finish_gemini.json
    output_path = os.path.join(folder_path, "check_finish_gemini.json")
    with open(output_path, 'w') as f:
        json.dump(unfinished_files, f, indent=4)
    
    print(f"\nSaved {len(unfinished_files)} unfinished files to {output_path}")
    print(f"Backup folder: {backup_folder}")

# Example usage
if __name__ == "__main__":
    # Replace with actual paths
    folder_path = "results"
    config_folder = "config_files"
    
    process_folder(folder_path, config_folder)