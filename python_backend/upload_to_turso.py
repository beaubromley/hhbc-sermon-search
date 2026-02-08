"""
Fast concurrent upload of local SQLite database to Turso.
Uses parallel HTTP connections to speed up the upload (~30-60 min instead of 18+ hours).

Usage: python upload_to_turso.py
"""
import sqlite3
import requests
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config import TURSO_DATABASE_URL, TURSO_AUTH_TOKEN_RW

LOCAL_DB = Path('data/database/transcripts.db')
BATCH_SIZE = 150  # rows per HTTP request (more rows = fewer round trips)
MAX_WORKERS = 8   # concurrent HTTP connections

# Convert libsql:// URL to https:// for the HTTP API
API_URL = TURSO_DATABASE_URL.replace('libsql://', 'https://') + '/v2/pipeline'

# Thread-local sessions for connection reuse within each thread
_thread_local = threading.local()


def _get_session():
    if not hasattr(_thread_local, 'session'):
        _thread_local.session = requests.Session()
        _thread_local.session.headers.update({
            'Authorization': f'Bearer {TURSO_AUTH_TOKEN_RW}',
            'Content-Type': 'application/json'
        })
    return _thread_local.session


def _turso_arg(v):
    if v is None:
        return {"type": "null", "value": None}
    elif isinstance(v, int):
        return {"type": "integer", "value": str(v)}
    elif isinstance(v, float):
        return {"type": "float", "value": v}
    else:
        return {"type": "text", "value": str(v)}


def execute(sql, args=None):
    """Execute a single SQL statement (used for DDL/setup, runs sequentially)."""
    stmt = {"type": "execute", "stmt": {"sql": sql}}
    if args:
        stmt["stmt"]["args"] = [_turso_arg(v) for v in args]
    body = {"requests": [stmt, {"type": "close"}]}
    resp = _get_session().post(API_URL, json=body)
    resp.raise_for_status()
    results = resp.json()["results"]
    if results[0].get("error"):
        raise Exception(results[0]["error"]["message"])
    return results[0]


def send_batch(statements):
    """Send a batch of statements in a single HTTP request (thread-safe)."""
    reqs = []
    for sql, args in statements:
        stmt = {"type": "execute", "stmt": {"sql": sql}}
        if args:
            stmt["stmt"]["args"] = [_turso_arg(v) for v in args]
        reqs.append(stmt)
    reqs.append({"type": "close"})
    body = {"requests": reqs}

    # Retry once on failure
    for attempt in range(2):
        try:
            resp = _get_session().post(API_URL, json=body)
            if not resp.ok:
                if attempt == 0:
                    time.sleep(1)
                    continue
                raise Exception(f"HTTP {resp.status_code}: {resp.text[:200]}")
            results = resp.json()["results"]
            for r in results:
                if r.get("error"):
                    raise Exception(r["error"]["message"])
            return
        except requests.exceptions.ConnectionError:
            if attempt == 0:
                time.sleep(2)
                continue
            raise


def upload_table(table_name, sql_template, columns, local_conn):
    """Upload a table using concurrent HTTP connections."""
    total = local_conn.execute(f'SELECT COUNT(*) FROM {table_name}').fetchone()[0]
    if total == 0:
        print(f"\n{table_name}: 0 rows, skipping.")
        return

    print(f"\nUploading {total:,} {table_name}...")

    # Read all rows and prepare batches
    cursor = local_conn.execute(f'SELECT * FROM {table_name}')
    batches = []
    while True:
        rows = cursor.fetchmany(BATCH_SIZE)
        if not rows:
            break
        stmts = [(sql_template, [r[c] for c in columns]) for r in rows]
        batches.append(stmts)

    uploaded = [0]
    errors = [0]
    lock = threading.Lock()
    start = time.time()

    def process_batch(batch):
        try:
            send_batch(batch)
            with lock:
                uploaded[0] += len(batch)
                current = uploaded[0]
                if current % 5000 < BATCH_SIZE or current >= total:
                    elapsed = time.time() - start
                    rate = current / elapsed if elapsed > 0 else 0
                    remaining = (total - current) / rate if rate > 0 else 0
                    print(f"  {current:,}/{total:,}  ({rate:.0f} rows/sec, ~{remaining:.0f}s left)")
        except Exception as e:
            with lock:
                errors[0] += 1
                if errors[0] <= 5:
                    print(f"  Error: {e}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        list(executor.map(process_batch, batches))

    elapsed = time.time() - start
    print(f"  Done: {uploaded[0]:,} rows in {elapsed:.1f}s. Errors: {errors[0]}")
    if errors[0] > 0:
        print(f"  WARNING: {errors[0]} batches failed. Some rows may be missing.")


def upload():
    local = sqlite3.connect(LOCAL_DB)
    local.row_factory = sqlite3.Row

    # Step 1: Drop and recreate tables (clean slate)
    print("Dropping existing tables...")
    for table in ['theological_topics', 'bible_references', 'transcript_segments', 'videos']:
        try:
            execute(f'DROP TABLE IF EXISTS {table}')
        except Exception as e:
            print(f"  Warning dropping {table}: {e}")
    print("  Done.")

    print("\nCreating tables...")
    execute('''CREATE TABLE IF NOT EXISTS videos (
        video_id TEXT PRIMARY KEY, title TEXT, duration INTEGER, url TEXT, date_published TEXT
    )''')
    execute('''CREATE TABLE IF NOT EXISTS transcript_segments (
        id INTEGER PRIMARY KEY, video_id TEXT, start_time REAL, end_time REAL,
        text TEXT, vimeo_url TEXT, FOREIGN KEY (video_id) REFERENCES videos (video_id)
    )''')
    execute('''CREATE TABLE IF NOT EXISTS bible_references (
        id INTEGER PRIMARY KEY, video_id TEXT, book TEXT, chapter INTEGER,
        verse_start INTEGER, verse_end INTEGER, start_time REAL, end_time REAL, context TEXT,
        FOREIGN KEY (video_id) REFERENCES videos (video_id)
    )''')
    execute('''CREATE TABLE IF NOT EXISTS theological_topics (
        id INTEGER PRIMARY KEY, video_id TEXT, topic TEXT, keyword_matched TEXT,
        start_time REAL, end_time REAL, context TEXT,
        FOREIGN KEY (video_id) REFERENCES videos (video_id)
    )''')

    # Create indexes
    execute('CREATE INDEX IF NOT EXISTS idx_segments_video ON transcript_segments(video_id)')
    execute('CREATE INDEX IF NOT EXISTS idx_bible_book ON bible_references(book)')
    execute('CREATE INDEX IF NOT EXISTS idx_bible_chapter ON bible_references(book, chapter)')
    execute('CREATE INDEX IF NOT EXISTS idx_bible_video ON bible_references(video_id)')
    execute('CREATE INDEX IF NOT EXISTS idx_topic ON theological_topics(topic)')
    execute('CREATE INDEX IF NOT EXISTS idx_topic_video ON theological_topics(video_id)')
    print("  Tables and indexes created.")

    # Step 2: Upload all tables concurrently
    start_total = time.time()

    upload_table('videos',
        'INSERT OR REPLACE INTO videos (video_id, title, duration, url, date_published) VALUES (?, ?, ?, ?, ?)',
        ['video_id', 'title', 'duration', 'url', 'date_published'],
        local)

    upload_table('transcript_segments',
        'INSERT OR REPLACE INTO transcript_segments (id, video_id, start_time, end_time, text, vimeo_url) VALUES (?, ?, ?, ?, ?, ?)',
        ['id', 'video_id', 'start_time', 'end_time', 'text', 'vimeo_url'],
        local)

    upload_table('bible_references',
        'INSERT OR REPLACE INTO bible_references (id, video_id, book, chapter, verse_start, verse_end, start_time, end_time, context) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        ['id', 'video_id', 'book', 'chapter', 'verse_start', 'verse_end', 'start_time', 'end_time', 'context'],
        local)

    upload_table('theological_topics',
        'INSERT OR REPLACE INTO theological_topics (id, video_id, topic, keyword_matched, start_time, end_time, context) VALUES (?, ?, ?, ?, ?, ?, ?)',
        ['id', 'video_id', 'topic', 'keyword_matched', 'start_time', 'end_time', 'context'],
        local)

    local.close()
    elapsed = time.time() - start_total
    print(f"\nUpload complete! Total time: {elapsed:.1f}s ({elapsed/60:.1f} min)")


if __name__ == '__main__':
    upload()
