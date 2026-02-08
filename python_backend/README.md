# HHBC Sermon Search - Python Backend

Data processing and export scripts.

## Setup

1. Create venv: `python -m venv venv`
2. Activate: `venv\Scripts\activate`
3. Install: `pip install -r requirements_local.txt`

## Export Data for Frontend

Run: `python export_to_json.py`

This exports the SQLite database to JSON files in `../frontend/public/data/`
