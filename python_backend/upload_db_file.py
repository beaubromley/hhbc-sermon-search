"""
Upload local SQLite database to Turso using the Platform API.
This creates a new database from a file upload (much faster than row-by-row HTTP inserts).

Usage:
  1. Get a Platform API token from https://app.turso.tech → Settings → API Tokens
  2. Run: python upload_db_file.py YOUR_API_TOKEN
"""
import requests
import sys
from pathlib import Path

DB_FILE = Path('data/database/transcripts.db')
ORG_NAME = 'beaubromley'  # Your Turso org/username
DB_NAME = 'hhbc-sermons'
GROUP = 'default'

if len(sys.argv) < 2:
    print("Usage: python upload_db_file.py YOUR_PLATFORM_API_TOKEN")
    print("\nGet your API token from: https://app.turso.tech → Settings → API Tokens")
    sys.exit(1)

API_TOKEN = sys.argv[1]
HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
}
BASE_URL = f'https://api.turso.tech/v1/organizations/{ORG_NAME}'


def main():
    # Step 1: Delete existing database
    print(f"Deleting existing database '{DB_NAME}'...")
    resp = requests.delete(f'{BASE_URL}/databases/{DB_NAME}', headers=HEADERS)
    if resp.ok:
        print("  Deleted.")
    elif resp.status_code == 404:
        print("  Not found (already deleted).")
    else:
        print(f"  Warning: {resp.status_code} - {resp.text[:200]}")

    # Step 2: Upload the dump file
    print(f"\nUploading {DB_FILE} ({DB_FILE.stat().st_size / 1024 / 1024:.1f} MB)...")
    with open(DB_FILE, 'rb') as f:
        resp = requests.post(
            f'{BASE_URL}/databases/dumps',
            headers=HEADERS,
            files={'file': (DB_FILE.name, f, 'application/octet-stream')}
        )
    if not resp.ok:
        print(f"  Upload failed: {resp.status_code} - {resp.text[:500]}")
        sys.exit(1)

    dump_url = resp.json().get('dump_url')
    print(f"  Uploaded. Dump URL received.")

    # Step 3: Create database from dump
    print(f"\nCreating database '{DB_NAME}' from dump...")
    resp = requests.post(
        f'{BASE_URL}/databases',
        headers={**HEADERS, 'Content-Type': 'application/json'},
        json={
            'name': DB_NAME,
            'group': GROUP,
            'seed': {
                'type': 'dump',
                'url': dump_url
            }
        }
    )
    if not resp.ok:
        print(f"  Failed: {resp.status_code} - {resp.text[:500]}")
        sys.exit(1)

    result = resp.json()
    print(f"  Database created!")
    print(f"\n  Hostname: {result.get('database', {}).get('Hostname', 'N/A')}")
    print(f"\nDone! Now go to the Turso dashboard to generate new tokens.")
    print(f"URL: https://app.turso.tech/{ORG_NAME}/databases/{DB_NAME}")


if __name__ == '__main__':
    main()
