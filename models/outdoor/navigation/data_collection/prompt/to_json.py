#!/usr/bin/env python3
"""
to_json.py

Usage:
    python to_json.py path/to/general_gen.py path/to/output.json

This script parses the given Python file, extracts the values of the variables
PROMPT and INSTRUCTION (assumed to be string literals), and writes them into
a JSON file with the structure:

{
    "prompt": <PROMPT string>,
    "instruction": <INSTRUCTION string>
}
"""

import ast
import json
import sys
from pathlib import Path
from outdoor.navigation.data_collection.prompt.general_gen import PROMPT, INSTRUCTION

def main():
    output_dict = {
        "prompt": PROMPT,
        "instruction": INSTRUCTION
    }
    with open("outdoor/navigation/data_collection/prompt/spot_and_question_gen_v2.json", "w", encoding="utf-8") as f:
        json.dump(output_dict, f, ensure_ascii=False, indent=4)
    # write JSON
    print(f"Wrote extracted data to JSON")

if __name__ == "__main__":
    main()