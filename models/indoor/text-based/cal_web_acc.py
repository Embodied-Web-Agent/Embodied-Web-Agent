import os
import json
from pathlib import Path
import difflib
import re

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

def check_add_to_cart_in_shopping_history(json_data):
    """
    Check if any item in shopping_history contains "Add to Cart"
    
    Args:
        json_data (dict): Parsed JSON data
    
    Returns:
        bool: True if "Add to Cart" is found in any shopping_history item
    """
    if 'shopping_history' not in json_data:
        return True  # No need to check if key doesn't exist

    shopping_history = json_data['shopping_history']
    if not isinstance(shopping_history, list):
        return False
    
    for item in shopping_history:
        if isinstance(item, str) and "Add to Cart" in item:
            return True
    
    return False

def check_json_file(json_data, file_name, config_folder):
    """
    Check if a JSON file meets all the specified conditions
    
    Returns:
        tuple: (bool, str) - (True if all conditions are met, description of conditions met)
    """
    if 'actions' not in json_data or 'observations' not in json_data:
        return False, "Missing actions or observations"
    
    actions = json_data['actions']
    observations = json_data['observations']
    
    # Track which conditions are met
    conditions_met = {
        "button_disabled": False,
        "95_percent_match": False,
        "add_to_cart": check_add_to_cart_in_shopping_history(json_data)
    }
    
    # Check condition 1: disabled Next button in observations
    for observation in observations:
        if isinstance(observation, str) and "button 'Next' disabled: True" in observation:
            conditions_met["button_disabled"] = True
            break
    

    for action in actions:
        environment = extract_environment_from_action(action)
        if environment:
            final_step = get_final_step_from_config(file_name, config_folder)

            if final_step and is_text_95_percent_similar(environment, final_step):
                conditions_met["95_percent_match"] = True
                break
    
    # Check if either of the original conditions is met
    original_condition_met = conditions_met["button_disabled"] or conditions_met["95_percent_match"]
    
    # Need to meet at least one original condition AND the add_to_cart condition (if needed)
    is_successful = original_condition_met and conditions_met["add_to_cart"]
    
    # Prepare reason message
    reasons = []
    if conditions_met["button_disabled"]:
        reasons.append("Button 'Next' disabled")
    if conditions_met["95_percent_match"]:
        reasons.append("95% match with final step")
    if conditions_met["add_to_cart"]:
        reasons.append("Add to Cart found")
    elif 'shopping_history' in json_data:
        reasons.append("Missing 'Add to Cart' in shopping history")
    
    if is_successful:
        return True, " & ".join(reasons)
    else:
        if not original_condition_met:
            return False, "No original conditions met"
        elif not conditions_met["add_to_cart"] and 'shopping_history' in json_data:
            return False, "Missing 'Add to Cart' requirement"
        else:
            return False, "Conditions not met"

def calculate_accuracy(folder_path, config_folder):
    """
    Calculate the accuracy of files meeting the specified conditions
    
    Args:
        folder_path (str): Path to the folder to process
        config_folder (str): Path to the config_files folder
    """
    folder = Path(folder_path)
    total_files = 0
    successful_files = 0
    results = {
        "button_disabled": 0,
        "95_percent_match": 0,
        "both": 0,
        "neither": 0
    }
    
    # For tracking scores of files 1-30
    numbered_scores = {"total": 0, "successful": 0}
    
    print(f"Processing files in: {folder_path}")
    print(f"Using config files from: {config_folder}")
    print("-" * 50)
    score_dict = dict()
    
    # Count all files in the directory first
    total_files_processed = sum(1 for _ in folder.iterdir())
    
    # Dictionary to store processed files to avoid duplicates
    processed_files = set()
    
    # First pass: Process files 1-30 (both regular and backup)
    for num in range(1, 31):
        # For files 1-30, look for both regular and backup versions
        regular_file_pattern = f"{num}.json_record.json"
        backup_file_pattern = f"{num}.json_record_backup.json"
        
        # Check for regular version
        regular_file_path = None
        for file_path in folder.iterdir():
            if regular_file_pattern == file_path.name:
                regular_file_path = file_path
                break
        
        # Check for backup version
        backup_file_path = None
        for file_path in folder.iterdir():
            if backup_file_pattern == file_path.name:
                backup_file_path = file_path
                break
        
        # Process regular version if it exists
        if regular_file_path:
            with open(regular_file_path, 'r') as f:
                data = json.load(f)
            
            config_folder2 = "config_files_shopping"
            is_finished, reason = check_json_file(data, regular_file_path.name, config_folder2)
            
            numbered_scores["total"] += 1
            if is_finished:
                numbered_scores["successful"] += 1
                successful_files += 1
            
            processed_files.add(str(regular_file_path))
            score_dict[str(regular_file_path)] = is_finished
            
            # print(f"{'✓' if is_finished else '✗'} {regular_file_path.name}: {reason}")
            
            if is_finished:
                if "Button 'Next' disabled" in reason and "95% match" in reason:
                    results["both"] += 1
                elif "Button 'Next' disabled" in reason:
                    results["button_disabled"] += 1
                elif "95% match" in reason:
                    results["95_percent_match"] += 1
            else:
                results["neither"] += 1
            
            total_files += 1
                
        # Process backup version if it exists
        if backup_file_path:
            try:
                with open(backup_file_path, 'r') as f:
                    data = json.load(f)
                
                is_finished, reason = check_json_file(data, backup_file_path.name, config_folder)
                
                numbered_scores["total"] += 1
                if is_finished:
                    numbered_scores["successful"] += 1
                    successful_files += 1
                
                processed_files.add(str(backup_file_path))
                score_dict[str(backup_file_path)] = is_finished
                
                # print(f"{'✓' if is_finished else '✗'} {backup_file_path.name}: {reason}")
                
                if is_finished:
                    if "Button 'Next' disabled" in reason and "95% match" in reason:
                        results["both"] += 1
                    elif "Button 'Next' disabled" in reason:
                        results["button_disabled"] += 1
                    elif "95% match" in reason:
                        results["95_percent_match"] += 1
                else:
                    results["neither"] += 1
                
                total_files += 1
                
            except Exception as e:
                print(f"⚠ Error processing {backup_file_path.name}: {str(e)}")
    
    # Second pass: Process files beyond 30 using preference for regular files
    for file_path in folder.iterdir():
        if str(file_path) in processed_files:
            continue  # Skip files we've already processed
            
        # Check if file has 'json' in its name
        if 'json' in file_path.name and file_path.is_file():
            file_name = file_path.name
            numbered_match = re.match(r'^(\d+)\.', file_name)
            
            # For files beyond 30, check if we need to process them
            if not numbered_match or int(numbered_match.group(1)) > 30:
                # For numbers > 30, check if we need to find a regular or backup version
                if numbered_match:
                    file_num = int(numbered_match.group(1))
                    regular_pattern = f"{file_num}.json_record.json"
                    
                    # If this is a backup file but we already processed the regular file, skip it
                    if "backup" in file_name:
                        regular_exists = False
                        for check_path in folder.iterdir():
                            if regular_pattern == check_path.name:
                                # Check if the regular file has already been processed
                                if str(check_path) in processed_files:
                                    regular_exists = True
                                    break
                        
                        if regular_exists:
                            continue  # Skip this backup file since regular exists and has been processed
                
                # Process this file
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    is_finished, reason = check_json_file(data, file_path.name, config_folder)
                    processed_files.add(str(file_path))
                    score_dict[str(file_path)] = is_finished
                    
                    # print(f"{'✓' if is_finished else '✗'} {file_path.name}: {reason}")
                    
                    if is_finished:
                        successful_files += 1
                        if "Button 'Next' disabled" in reason and "95% match" in reason:
                            results["both"] += 1
                        elif "Button 'Next' disabled" in reason:
                            results["button_disabled"] += 1
                        elif "95% match" in reason:
                            results["95_percent_match"] += 1
                    else:
                        results["neither"] += 1
                    
                    total_files += 1
                    
                except Exception as e:
                    print(f"⚠ Error processing {file_path.name}: {str(e)}")

    with open("web_score.json", "w") as f:
        json.dump(score_dict, f)
        
    # Calculate accuracy
    accuracy = (successful_files / total_files * 100) if total_files > 0 else 0
    
    # Calculate accuracy for numbered files
    numbered_accuracy = 0
    if numbered_scores["total"] > 0:
        numbered_accuracy = (numbered_scores["successful"] / numbered_scores["total"] * 100)
    
    # Verify counts match
    total_conditions = results["button_disabled"] + results["95_percent_match"] + results["both"] + results["neither"]
    if total_conditions != total_files:
        print("WARNING: Internal count mismatch detected!")
    
    print("-" * 50)
    print(f"\nSUMMARY:")
    print(f"Total files in directory: {total_files_processed}")
    print(f"Total JSON files processed: {total_files}")
    print(f"Files meeting all criteria: {successful_files}")
    print(f"Overall Accuracy: {accuracy:.2f}%")
    print(f"\nBreakdown by condition:")
    print(f"  Button 'Next' disabled only: {results['button_disabled']}")
    print(f"  95% match with final step only: {results['95_percent_match']}")
    print(f"  Both conditions met: {results['both']}")
    print(f"  No conditions met: {results['neither']}")
    
    print(f"\nFiles 1-30 Accuracy:")
    print(f"  Score: {numbered_accuracy:.2f}% ({numbered_scores['successful']}/{numbered_scores['total']})")

# Example usage
if __name__ == "__main__":
    # Replace with actual paths
    folder_path = "results"
    config_folder = "config_files"
    
    calculate_accuracy(folder_path, config_folder)