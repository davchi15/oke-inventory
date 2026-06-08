# Oke Inventory

An AI-powered inventory management system built by Oke Works.
Check items in and out of storage using a web interface, CLI, camera, and voice commands.

## Features
- Add, list, and update inventory items
- Check items in and out with full transaction history
- Web UI accessible from any browser
- CLI for quick terminal access
- SQLite local database — no internet required

## Setup

### Requirements
- Python 3.10+
- pip

### Install dependencies
pip install flask

### Run the web app
python app.py

Then open http://localhost:5000 in your browser.

### Run the CLI
python cli.py

## Project Structure
- app.py — Flask app entry point
- routes.py — Web routes
- db.py — Database functions
- cli.py — Command line interface
- Item.py — Item data model
- enums.py — Action enum for transactions
- templates/ — HTML templates
- static/ — CSS styles

## Built with
- Python 3.10+
- Flask
- SQLite
- YOLOv8 (coming soon)
- Whisper (coming soon)