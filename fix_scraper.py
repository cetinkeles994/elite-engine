
import sys

file_path = r'C:\Users\cetin\Desktop\VALUE\scraper_engine.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Fix the dropping_odds assignment
    if "match['dropping_odds'] = { 'side': 'home'" in line:
        line = line.replace("match['dropping_odds']", "drop_info")
    if "match['dropping_odds'] = { 'side': 'away'" in line:
        line = line.replace("match['dropping_odds']", "drop_info")
    # Lower threshold
    if "if drop_pct > 2.0:" in line:
        line = line.replace("2.0", "1.1")
    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Fix applied successfully via script.")
