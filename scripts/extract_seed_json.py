"""Extract JSON prediction data from seed_localstorage.js into a static file."""
import json
import re

with open("scripts/seed_localstorage.js", "r", encoding="utf-8") as f:
    content = f.read()

match = re.search(r"const data = (\[.*?\]);", content, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    with open("frontend/public/seed_predictions.json", "w", encoding="utf-8") as out:
        json.dump(data, out, ensure_ascii=False)
    print(f"OK: {len(data)} predictions saved to frontend/public/seed_predictions.json")
else:
    print("FAIL: could not extract data from seed_localstorage.js")
