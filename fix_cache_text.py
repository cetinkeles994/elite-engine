
import json
import os

CACHE_FILES = ["matches_cache.json", "history_cache.json"]

def fix_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"Processing {filepath}...")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Simple string replacement is safer and faster for this specific typo
        if "MONTE CARLO SİMÜLASYONU (1000 Maç)" in content:
            new_content = content.replace(
                "MONTE CARLO SİMÜLASYONU (1000 Maç)", 
                "MONTE CARLO SİMÜLASYONU (10.000 Maç)"
            )
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            print(f"Fixed {filepath} successfully.")
        else:
            print(f"No occurrences found in {filepath}.")
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    for f in CACHE_FILES:
        fix_file(f)
