from item import Item
from storage import save_items, load_items

# Load existing items from file
items = load_items()
newItem = False
# Add new items if starting fresh
if len(items) == 0:
    items.append(Item("Screwdriver", 3, "Tools"))
    items.append(Item("Arduino Uno", 2, "Electronics"))
    items.append(Item("Wire Spool", 5, "Electronics"))
    newItem = True
# Print as a list
print("\n--- Item List ---")
for item in items:
    print(item)

# Convert to dict keyed by name
items_dict = {item.name: item for item in items}

# Print from dict — access a specific item by name
print("\n--- Dict Lookup ---")
print(items_dict["Screwdriver"])

# Save to JSON
if(newItem == True):
    save_items(items)
    
