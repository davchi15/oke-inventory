from item import Item
from datetime import datetime


item = Item("Screwdriver", 3, "Tools")
item.last_accessed = datetime(2026, 6, 1, 10, 30)  # June 1st, 2026 at 10:30am
item2 = Item("Wrench",1,"Tools")
item2.last_accessed = datetime(2026, 6, 1, 10, 30)  # June 1st, 2026 at 10:30am
item3 = Item("Screws", 5, "Tools")
item3.last_accessed = datetime(2026, 6, 1, 10, 30)  # June 1st, 2026 at 10:30am


print(item.name)