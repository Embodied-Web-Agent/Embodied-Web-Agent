import json
import os
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

def extract_final_states(object_final_states):
    """Extract properties from Object Final States (keeping parentReceptacles)"""
    final_states_list = []
    for obj in object_final_states:
        object_name = obj["object"]
        changes = obj["changes"]
        
        # Create list items for each property including parentReceptacles
        for key, value in changes.items():
            final_states_list.append([object_name, key, value])
    
    return final_states_list

def all_ground_truth_found(state_eval_list, ground_truth_list):
    """Check if all ground truth states are found in evaluated states"""
    # Convert lists to sets of tuples for comparison
    state_eval_set = set(tuple(state) for state in state_eval_list)
    ground_truth_set = set(tuple(state) for state in ground_truth_list)
    
    # Check if all ground truth items are found in evaluated items
    return ground_truth_set.issubset(state_eval_set)

def calculate_percentage_found(state_eval_list, ground_truth_list):
    """Calculate what percentage of ground truth states are found in evaluated states"""
    if not ground_truth_list:
        return 100.0  # If there's nothing to find, 100% is found
    
    # Convert lists to sets of tuples for comparison
    state_eval_set = set(tuple(state) for state in state_eval_list)
    ground_truth_set = set(tuple(state) for state in ground_truth_list)
    
    # Count how many ground truth states are found
    found_states = len(ground_truth_set.intersection(state_eval_set))
    total_ground_truth_states = len(ground_truth_set)
    
    return (found_states / total_ground_truth_states) * 100

def main():
    results_dir = Path("results")
    revised_dir = Path("revised_states")
    
    # Tracking for all files
    total_tasks = 0
    all_found_count = 0
    percentage_scores = []
    score_dict = dict()
    
    # Special tracking for files 1-30
    numbered_stats = {
        "total": 0,
        "all_found": 0,
        "percentages": []
    }
    
    # First, process files 1-30 - calculate for both primary and backup files
    for i in range(1, 31):  # 1 to 30 inclusive
        base_name = f"{i}.json_record"
        primary_file = results_dir / f"{base_name}.json"
        backup_file = results_dir / f"{base_name}_backup.json"
        
        # Find revised file (ground truth)
        revised_file = revised_dir / f"{i}.json"

        if not revised_file.exists():
            continue
            
        try:
            # Load revised file (ground truth)
            with open(revised_file, 'r') as f:
                revised_data = json.load(f)
                
            # Get Object Final States from revised file (ground truth)
            if "Object Final States" not in revised_data:
                continue
                
            object_final_states = revised_data["Object Final States"]
            ground_truth_states = extract_final_states(object_final_states)
            
            # Process primary file if it exists
            if primary_file.exists():
                try:
                    with open(primary_file, 'r') as f:
                        result_data = json.load(f)

                    revised_file = f"revised_states_shopping/{i}.json"
                    
                    with open(revised_file, 'r') as f:
                        revised_data = json.load(f)
                        
                    # Get Object Final States from revised file (ground truth)
                    if "Object Final States" not in revised_data:
                        continue
                        
                    object_final_states = revised_data["Object Final States"]
                    ground_truth_states = extract_final_states(object_final_states)                    
                    
                    if "state_evaluator" in result_data:
                        state_evaluator = result_data["state_evaluator"]
                        processed_state_eval = process_state_evaluator(state_evaluator)
                        
                        # Update numbered stats
                        numbered_stats["total"] += 1
                        total_tasks += 1
                        
                        # Check metrics
                        if all_ground_truth_found(processed_state_eval, ground_truth_states):
                            numbered_stats["all_found"] += 1
                            all_found_count += 1
                        
                        percentage = calculate_percentage_found(processed_state_eval, ground_truth_states)
                        numbered_stats["percentages"].append(percentage)
                        percentage_scores.append(percentage)
                        score_dict[str(primary_file)] = percentage
                except Exception as e:
                    print(f"Error processing primary file {i}: {str(e)}")
            
            # Process backup file if it exists
            if backup_file.exists():
                try:
                    with open(backup_file, 'r') as f:
                        result_data = json.load(f)
                    
                    if "state_evaluator" in result_data:
                        state_evaluator = result_data["state_evaluator"]
                        processed_state_eval = process_state_evaluator(state_evaluator)
                        
                        # Update numbered stats
                        numbered_stats["total"] += 1
                        total_tasks += 1
                        
                        # Check metrics
                        if all_ground_truth_found(processed_state_eval, ground_truth_states):
                            numbered_stats["all_found"] += 1
                            all_found_count += 1
                        
                        percentage = calculate_percentage_found(processed_state_eval, ground_truth_states)
                        numbered_stats["percentages"].append(percentage)
                        percentage_scores.append(percentage)
                        score_dict[str(backup_file)] = percentage
                except Exception as e:
                    print(f"Error processing backup file {i}: {str(e)}")
                    
        except Exception as e:
            print(f"Error processing revised file {i}: {str(e)}")
    
    # Now process files 31-880 using the original logic
    for i in range(31, 881):
        # Find result file using the original find_json_file method
        result_file = find_json_file(results_dir, i)
        if result_file is None:
            continue
        
        # Find revised file (ground truth)
        revised_file = revised_dir / f"{i}.json"
        if not revised_file.exists():
            continue
        
        try:
            # Load result file
            with open(result_file, 'r') as f:
                result_data = json.load(f)
            
            # Load revised file (ground truth)
            with open(revised_file, 'r') as f:
                revised_data = json.load(f)
            
            # Get state_evaluator from result file
            if "state_evaluator" not in result_data:
                continue
            
            state_evaluator = result_data["state_evaluator"]
            processed_state_eval = process_state_evaluator(state_evaluator)
            
            # Get Object Final States from revised file (ground truth)
            if "Object Final States" not in revised_data:
                continue
            
            object_final_states = revised_data["Object Final States"]
            ground_truth_states = extract_final_states(object_final_states)
            
            total_tasks += 1
            
            # Check if all ground truth states are found (metric 1)
            if all_ground_truth_found(processed_state_eval, ground_truth_states):
                all_found_count += 1
            
            # Calculate percentage of ground truth states found (metric 2)
            percentage = calculate_percentage_found(processed_state_eval, ground_truth_states)
            percentage_scores.append(percentage)
            score_dict[str(result_file)] = percentage
            
        except Exception as e:
            print(f"Error processing file {i}: {str(e)}")
            continue
    
    # Calculate averages for all files
    if total_tasks > 0:
        avg_all_found_accuracy = all_found_count / total_tasks
        avg_percentage_found = sum(percentage_scores) / len(percentage_scores) if percentage_scores else 0.0
    else:
        avg_all_found_accuracy = 0.0
        avg_percentage_found = 0.0
    
    # Calculate averages for files 1-30
    numbered_avg_all_found = 0.0
    numbered_avg_percentage = 0.0
    if numbered_stats["total"] > 0:
        numbered_avg_all_found = numbered_stats["all_found"] / numbered_stats["total"]
        numbered_avg_percentage = sum(numbered_stats["percentages"]) / numbered_stats["total"] if numbered_stats["percentages"] else 0.0
    
    # Save results
    with open("embodied_score_gpt.json", 'w') as f:
        json.dump(score_dict, f, indent=2)
    
    print(f"\nGround Truth Coverage Metrics:")
    print(f"Total tasks compared: {total_tasks}")
    print(f"Tasks where all ground truth states were found: {all_found_count}")
    print(f"Average accuracy (all ground truth states found): {avg_all_found_accuracy:.3f}")
    print(f"Average percentage of ground truth states found: {avg_percentage_found:.2f}%")
    
    print(f"\nFiles 1-30 Metrics:")
    print(f"  Total files: {numbered_stats['total']}")
    print(f"  All ground truth found: {numbered_stats['all_found']}")
    print(f"  Average accuracy: {numbered_avg_all_found:.3f}")
    print(f"  Average percentage found: {numbered_avg_percentage:.2f}%")

if __name__ == "__main__":
    main()