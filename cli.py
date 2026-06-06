from db import create_table, add_item, get_all_items, update_quantity, check_in, check_out, get_history
from item import Item
from enums import Action

def run_cli():
    create_table()
    print("\nWelcome to Oke Inventory")
    print("Commands: add | list | update | checkout | checkin | history | quit\n")

    while True:
        command = input("Enter command: ").strip().lower()

        match command:
            case "add":
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

            case "list":
                items = get_all_items()
                if len(items) == 0:
                    print("\n  No items in inventory.")
                else:
                    print("\n  -- Current Inventory --")
                    for item in items:
                        print(f"  {item}")
                    print()

            case "update":
                print("\n  -- Update Item Quantity --")
                name = input("  Item name: ").strip()
                items = get_all_items()
                match_item = next((i for i in items if i.name.lower() == name.lower()), None)

                if match_item is None:
                    print(f"  Item '{name}' not found.")
                else:
                    print(f"  Current quantity: {match_item.quantity}")
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

            case "checkout":
                print("\n  -- Check Out Item --")
                name = input("  Item name: ").strip()
                check_out(name)

            case "checkin":
                print("\n  -- Check In Item --")
                name = input("  Item name: ").strip()
                check_in(name)

            case "history":
                print("\n  -- Transaction History --")
                name = input("  Item name: ").strip()
                rows = get_history(name)
                if len(rows) == 0:
                    print(f"  No transactions found for '{name}'.")
                else:
                    print(f"\n  History for '{name}':")
                    for action, timestamp in rows:
                        label = "Checked Out" if action == Action.CHECK_OUT else "Checked In"
                        print(f"  {label} — {timestamp}")
                    print()

            case "quit":
                print("Goodbye!")
                break

            case _:
                print("  Unknown command. Try: add | list | update | checkout | checkin | history | quit")

if __name__ == "__main__":
    run_cli()