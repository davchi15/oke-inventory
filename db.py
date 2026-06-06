import sqlite3
from datetime import datetime
from item import Item
from enums import Action

DB_FILE = "inventory.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def create_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL,
                category TEXT NOT NULL,
                last_accessed TEXT NOT NULL
            )
        """)
    create_transactions_table()

    print("Database ready.")

def add_item(item):
    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO items (name, quantity, category, last_accessed)
                VALUES (?, ?, ?, ?)
            """, (item.name, item.quantity, item.category,
                  item.last_accessed.strftime('%Y-%m-%d %H:%M')))
        print(f"Added: {item.name}")
    except sqlite3.IntegrityError:
        print(f"Item '{item.name}' already exists.")

def get_all_items():
    with get_connection() as conn:
        rows = conn.execute("SELECT name, quantity, category, last_accessed FROM items").fetchall()
    return [Item.from_dict({
        "name": r[0], "quantity": r[1],
        "category": r[2], "last_accessed": r[3]
    }) for r in rows]


def update_quantity(name, new_quantity):
    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE items SET quantity = ?, last_accessed = ?
            WHERE name = ?
        """, (new_quantity, datetime.now().strftime('%Y-%m-%d %H:%M'), name))
    if cursor.rowcount == 0:
        print(f"Item '{name}' not found.")
    else:
        print(f"Updated '{name}' quantity to {new_quantity}.")


def create_transactions_table():
    with get_connection() as conn:
        conn.execute(""" 
                     CREATE TABLE IF NOT EXISTS transactions (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     item_name TEXT NOT NULL,
                     action TEXT NOT NULL,
                     timestamp TEXT NOT NULL)""")
        
def log_transaction(item_name, action):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO transactions (item_name, action, timestamp)
            VALUES (?, ?, ?)
        """, (item_name, action, datetime.now().strftime('%Y-%m-%d %H:%M')))

def check_out(name):
    items = get_all_items()
    match = next((i for i in items if i.name.lower() == name.lower()), None)

    if match is None:
        print(f"  Item '{name}' not found in inventory.")
        return False
    if match.quantity <= 0:
        print(f"  Cannot check out '{name}' — quantity is 0.")
        return False

    update_quantity(match.name, match.quantity - 1)
    log_transaction(match.name, "check_out")
    print(f"  '{match.name}' checked out. {match.quantity - 1} remaining.")
    return True

def check_in(name):
    items = get_all_items()
    match = next((i for i in items if i.name.lower() == name.lower()), None)

    if match is None:
        print(f"  Item '{name}' not found in inventory.")
        return False

    update_quantity(match.name, match.quantity + 1)
    log_transaction(match.name, "check_in")
    print(f"  '{match.name}' checked in. {match.quantity + 1} now in storage.")
    return True

def get_history(name):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT action, timestamp FROM transactions
            WHERE LOWER(item_name) = LOWER(?)
            ORDER BY timestamp DESC
        """, (name,)).fetchall()
    return rows