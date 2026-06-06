import sqlite3
from datetime import datetime
from item import Item

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