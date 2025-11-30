import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Union

# !!! SET YOUR FILE PATH HERE !!!
DATA_PATH = r"C:\Users\User\Downloads\AGENTIC AI\A3\n8n\shared\region1.json"

def analyze_structure(data: Any) -> Union[str, Dict[str, Any], List[Any]]:
    """Recursively analyzes the structure of a JSON object or list."""
    
    if isinstance(data, dict):
        structure = {}
        for key, value in data.items():
            structure[key] = analyze_structure(value)
        return structure
    
    elif isinstance(data, list):
        if not data:
            return ["<EMPTY_LIST>"]
        
        # Analyze the structure of the first item in the list
        first_item_structure = analyze_structure(data[0])
        
        # Check if all items in the list share the same structure/type
        all_same_type = all(isinstance(item, type(data[0])) for item in data)
        
        if all_same_type:
             # If all items are objects, show the structure of the object
             if isinstance(data[0], dict):
                 return [first_item_structure]
             # If all items are primitives (string, int, etc.), show the type
             else:
                 return [f"<{type(data[0]).__name__.upper()}>"]
        else:
            # If the list contains mixed types, just list the types found
            return [f"<{type(item).__name__.upper()}>" for item in data]
            
    # For primitive types (int, str, bool, float, None)
    else:
        # Special handling for None (which can be a big problem)
        if data is None:
            return "<NULL>"
        return f"<{type(data).__name__.upper()}>"

def get_json_structure(path: str) -> None:
    """Main function to load and print the structure."""
    if not os.path.exists(path):
        print(f"❌ ERROR: File not found at path: {path}")
        return

    try:
        with open(path, 'r') as f:
            data = json.load(f)
            
        print("-" * 50)
        print(f"✅ ANALYSIS OF: {os.path.basename(path)}")
        print(f"--- ROOT TYPE: <{type(data).__name__.upper()}> ---")
        print("-" * 50)
        
        structure = analyze_structure(data)
        
        # Use json.dumps for pretty printing the structure dictionary
        print(json.dumps(structure, indent=4, sort_keys=False))
        
        print("-" * 50)

    except json.JSONDecodeError as e:
        print(f"❌ CRITICAL ERROR: Invalid JSON format. Line {e.lineno}, Col {e.colno}. Ensure n8n is writing valid JSON.")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    get_json_structure(DATA_PATH)