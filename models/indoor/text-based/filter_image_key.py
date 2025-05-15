import os
import json
from pathlib import Path

# Directory containing the JSON files
directory_path = './results_qwen'  # Change this to your folder path

def process_json_file(file_path):
    """Process a single JSON file to extract text from observations and delete the original."""
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        
        # Check if observations key exists and is a list
        if not isinstance(json_data.get('observations'), list):
            print(f"File {file_path} does not have valid observations array.")
            return
        
        # Extract only the text key from each observation, but keep all other keys intact
        extracted_data = json_data.copy()  # Copy all keys from original JSON
        
        # Replace only the observations array with the filtered version
        
        extracted_data['observations'] = [
            {'text': obs['text']} if isinstance(obs, dict) and 'text' in obs else obs
            for obs in json_data['observations']
        ]
        
        # Create backup filename
        path_obj = Path(file_path)
        backup_file_path = path_obj.parent / f"{path_obj.stem}_backup{path_obj.suffix}"
        
        # Write to backup file
        with open(backup_file_path, 'w', encoding='utf-8') as backup_file:
            json.dump(extracted_data, backup_file, indent=2)
        
        # Verify backup file exists before deleting original
        if backup_file_path.exists():
            # Delete the original file
            os.remove(file_path)
            print(f"Processed {file_path} -> {backup_file_path} and deleted original")
        else:
            print(f"Error: Backup file {backup_file_path} was not created, original preserved")
    
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")

def main():
    try:
        # Convert to absolute path to avoid relative path issues
        abs_dir_path = os.path.abspath(directory_path)
        
        # Get all JSON files in the directory
        json_files = [f for f in os.listdir(abs_dir_path) 
                    if f.lower().endswith('.json') and ("backup" not in f) and ("config" not in f) and int(f.split(".")[0]) <= 46 and os.path.isfile(os.path.join(abs_dir_path, f))]
        
        if not json_files:
            print("No JSON files found in the directory.")
            return
        
        print(f"Found {len(json_files)} JSON file(s). Processing...")
        
        # Process each JSON file
        for file in json_files:
            file_path = os.path.join(abs_dir_path, file)
            process_json_file(file_path)
        
        print("Processing complete.")
    
    except Exception as e:
        print(f"Error reading directory: {str(e)}")

if __name__ == "__main__":
    main()