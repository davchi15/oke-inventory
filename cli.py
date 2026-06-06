from db import create_table, add_item, get_all_items, update_quantity
from item import Item

def run_cli():
    create_table()
    print("\nOke Inventory CLI")
    print("Commands: add | list | update | quit\n")

    while True:
        command = input("Enter command: ").strip().lower()

        if command == "add":
            print("\n  -- Add New Item --")
            name = input("  Item name: ").strip()

            while True:
                try:
                    quantity = int(input("  Quantity (numbers only): ").strip())
                    if quantity < 0:
                        print("  Quantity can't be negative, try again.")
                        continue
                    break
                except ValueError:
                    print("  Please enter a valid number.")

            print("  Categories: Tools | Electronics | Components | Other")
            category = input("  Category: ").strip().title()

            print(f"\n  Adding: {name} | Qty: {quantity} | Category: {category}")
            confirm = input("  Confirm? (y/n): ").strip().lower()

            if confirm == "y":
                add_item(Item(name, quantity, category))
            else:
                print("  Cancelled.")

        elif command == "list":
            items = get_all_items()
            if len(items) == 0:
                print("\n  No items in inventory.")
            else:
                print("\n  -- Current Inventory --")
                for item in items:
                    print(f"  {item}")
                print()

        elif command == "update":
            print("\n  -- Update Item Quantity --")
            name = input("  Item name: ").strip()
            items = get_all_items()
            match = next((i for i in items if i.name.lower() == name.lower()), None)

            if match is None:
                print(f"  Item '{name}' not found.")
            else:
                print(f"  Current quantity: {match.quantity}")
                while True:
                    try:
                        new_qty = int(input("  New quantity: ").strip())
                        if new_qty < 0:
                            print("  Quantity can't be negative.")
                            continue
                        break
                    except ValueError:
                        print("  Please enter a valid number.")
                update_quantity(name, new_qty)

        elif command == "quit":
            print("Goodbye!")
            break

        else:
            print("  Unknown command. Try: add | list | update | quit")

if __name__ == "__main__":
    run_cli()