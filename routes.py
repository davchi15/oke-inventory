from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import add_item, get_all_items, check_in, check_out, get_history
from Item import Item

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    try:
        items = get_all_items()
        return render_template("index.html", items=items)
    except Exception as e:
        print(f"  Error loading inventory: {e}")
        return render_template("index.html", items=[])

@bp.route("/add", methods=["POST"])
def add():
    try:
        name = request.form.get("name", "").strip()
        quantity = int(request.form.get("quantity", 0))
        category = request.form.get("category", "Other").strip().title()
        if not name:
            raise ValueError("Item name cannot be empty.")
        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        add_item(Item(name, quantity, category))
    except ValueError as e:
        print(f"  Validation error: {e}")
    except Exception as e:
        print(f"  Error adding item: {e}")
    return redirect(url_for("main.index"))

@bp.route("/checkin/<name>")
def checkin(name):
    try:
        if not name or not name.strip():
            raise ValueError("Item name cannot be empty.")
        check_in(name)
    except ValueError as e:
        print(f"  Validation error: {e}")
    except Exception as e:
        print(f"  Error checking in '{name}': {e}")
    return redirect(url_for("main.index"))

@bp.route("/checkout/<name>")
def checkout(name):
    try:
        if not name or not name.strip():
            raise ValueError("Item name cannot be empty.")
        check_out(name)
    except ValueError as e:
        print(f"  Validation error: {e}")
    except Exception as e:
        print(f"  Error checking out '{name}': {e}")
    return redirect(url_for("main.index"))

@bp.route("/history/<name>")
def history(name):
    try:
        if not name or not name.strip():
            raise ValueError("Item name cannot be empty.")
        rows = get_history(name)
        return render_template("history.html", name=name, rows=rows)
    except ValueError as e:
        print(f"  Validation error: {e}")
        return redirect(url_for("main.index"))
    except Exception as e:
        print(f"  Error loading history for '{name}': {e}")
        return render_template("history.html", name=name, rows=[])