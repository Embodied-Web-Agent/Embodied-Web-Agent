import json
import os
import random
from pathlib import Path

def find_json_file(results_dir, number):
    """Find the appropriate JSON file for a given number"""
    base_name = f"{number}.json_record"
    primary_file = results_dir / f"{base_name}.json"
    backup_file = results_dir / f"{base_name}_backup.json"
    
    if primary_file.exists():
        return primary_file
    elif backup_file.exists():
        return backup_file
    else:
        return None

def process_state_evaluator(state_evaluator):
    """Process state_evaluator list, replacing isBroken with isSliced"""
    processed_list = []
    for item in state_evaluator:
        object_name, property_name, value = item
        if property_name == "isBroken":
            property_name = "isSliced"
        processed_list.append([object_name, property_name, value])
    return processed_list

def load_config_file(config_dir, number):
    """Load config file for a given number"""
    config_file = config_dir / f"{number}.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return None

def extract_final_states(object_final_states):
    """Extract properties without parentReceptacles from Object Final States for comparison"""
    final_states_list = []
    for obj in object_final_states:
        object_name = obj["object"]
        changes = obj["changes"].copy()  # Make a copy to avoid modifying original
        
        # Remove parentReceptacles from the copy for comparison
        if "parentReceptacles" in changes:
            del changes["parentReceptacles"]
        
        # Create list items for each property
        for key, value in changes.items():
            final_states_list.append([object_name, key, value])
    
    return final_states_list

def compare_lists(state_eval_list, final_states_list):
    """Compare two lists to see if they are exactly the same"""
    # Sort both lists for comparison
    state_eval_sorted = sorted(state_eval_list)
    final_states_sorted = sorted(final_states_list)
    
    return state_eval_sorted == final_states_sorted

def check_has_parent_receptacles(config_data):
    """Check if any object in config data has parentReceptacles"""
    if "Object Final States" not in config_data:
        return False
    
    for obj in config_data["Object Final States"]:
        if "changes" in obj and "parentReceptacles" in obj["changes"]:
            return True
    return False

def save_config_file(config_data, revised_dir, number, remove_receptacles=False):
    """Save either original or revised config file based on random probability"""
    # Check if the original file has parentReceptacles
    had_parent_receptacles = check_has_parent_receptacles(config_data)
    
    if remove_receptacles:
        # Create a revised version without parentReceptacles
        revised_config = json.loads(json.dumps(config_data))  # Deep copy
        if "Object Final States" in revised_config:
            for obj in revised_config["Object Final States"]:
                if "changes" in obj and "parentReceptacles" in obj["changes"]:
                    del obj["changes"]["parentReceptacles"]
        data_to_save = revised_config
        actually_changed = had_parent_receptacles
    else:
        # Save the original config
        data_to_save = config_data
        actually_changed = False
    
    # Save the file
    output_file = revised_dir / f"{number}.json"
    with open(output_file, 'w') as f:
        json.dump(data_to_save, f, indent=2)
    
    return had_parent_receptacles, actually_changed

def main():
    results_dir = Path("results")
    config_dir = Path("config_files")
    revised_dir = Path("revised_states")
    
    # Create revised_states directory if it doesn't exist
    revised_dir.mkdir(exist_ok=True)
    
    finished_tasks = []
    finished_count = 0
    files_with_parent_receptacles = 0
    files_changed = 0
    files_unchanged = 0
    attempted_to_change = 0
    total_files_saved = 0
    
    for i in range(1, 881):  # 1 to 880 inclusive
        # Find and load results file
        results_file = find_json_file(results_dir, i)
        if results_file is None:
            continue
        
        try:
            with open(results_file, 'r') as f:
                results_data = json.load(f)
            
            # Load config file
            config_data = load_config_file(config_dir, i)
            if config_data is None:
                continue
            
            # Check if task is finished
            is_task_finished = False
            remove_receptacles = False
            
            if "state_evaluator" in results_data and "Object Final States" in config_data:
                state_evaluator = results_data["state_evaluator"]
                processed_state_eval = process_state_evaluator(state_evaluator)
                object_final_states = config_data["Object Final States"]
                final_states_list = extract_final_states(object_final_states)
                
                if compare_lists(processed_state_eval, final_states_list):
                    is_task_finished = True
                    finished_count += 1
                    finished_tasks.append(results_file.stem)
                    print(f"this task is finished for {results_file.name}")
                    
                    # For finished tasks, randomly decide whether to remove parentReceptacles
                    remove_receptacles = random.random() < 0.3
                    if remove_receptacles:
                        attempted_to_change += 1
            
            # Save config file (all files, but modify only if remove_receptacles is True)
            had_parent_receptacles, actually_changed = save_config_file(config_data, revised_dir, i, remove_receptacles)
            total_files_saved += 1
            
            # Track statistics
            if had_parent_receptacles:
                files_with_parent_receptacles += 1
            
            if actually_changed:
                files_changed += 1
            else:
                files_unchanged += 1
        
        except Exception as e:
            print(f"Error processing file {i}: {str(e)}")
            continue
    
    # Save results
    output_data = {
        "finished_count": finished_count,
        "finished_tasks": finished_tasks,
        "files_with_parent_receptacles": files_with_parent_receptacles,
        "files_changed": files_changed,
        "files_unchanged": files_unchanged,
        "attempted_to_change": attempted_to_change,
        "total_files_saved": total_files_saved
    }
    
    with open("results_del_recep.json", 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nTotal finished tasks: {finished_count}")
    print(f"Total files saved: {total_files_saved}")
    print(f"Files that originally had parentReceptacles: {files_with_parent_receptacles}")
    print(f"Files actually changed (parentReceptacles removed): {files_changed}")
    print(f"Files unchanged: {files_unchanged}")
    print(f"Attempted to change: {attempted_to_change}")
    print(f"Results saved to results_del_recep.json")
    print(f"Config files saved to {revised_dir}")

if __name__ == "__main__":
    main()