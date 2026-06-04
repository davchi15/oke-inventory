import json
import os
from item import Item

FILE = "inventory.json"


def save_items(items):
    with open(FILE,"w") as f:
        json.dump([item.to_dict() for item in items], f, indent =2)
    print(f"Saved {len(items)} items to {FILE}")


def load_items():
    if not os.path.exists(FILE):
        print("No inventory file found, starting fresh.")
        return []
    
    with open(FILE, "r") as f:
        data = json.load(f)
    items = [Item.from_dict(d) for d in data]
    print(f"Loaded {len(items)} items from {FILE}")
    return items