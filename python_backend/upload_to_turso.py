"""
Sync local SQLite database to Turso.
Default: incremental (only uploads new videos). Use --full for a complete re-upload.

Usage:
  python upload_to_turso.py          # incremental sync
  python upload_to_turso.py --full   # drop everything and re-upload
"""
import sqlite3
import requests
import sys
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from src.config import TURSO_DATABASE_URL, TURSO_AUTH_TOKEN_RW

LOCAL_DB = Path('data/database/transcripts.db')
BATCH_SIZE = 150
MAX_WORKERS = 8

API_URL = TURSO_DATABASE_URL.replace('libsql://', 'https://') + '/v2/pipeline'

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
    """Execute a single SQL statement."""
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


def query_rows(sql, args=None):
    """Execute a query and return rows as list of dicts."""
    result = execute(sql, args)
    rows_data = result.get("response", {}).get("result", {}).get("rows", [])
    cols = [c["name"] for c in result.get("response", {}).get("result", {}).get("cols", [])]
    rows = []
    for row in rows_data:
        obj = {}
        for i, cell in enumerate(row):
            if cell.get("type") == "null":
                obj[cols[i]] = None
            elif cell.get("type") == "integer":
                obj[cols[i]] = int(cell["value"])
            elif cell.get("type") == "float":
                obj[cols[i]] = float(cell["value"])
            else:
                obj[cols[i]] = cell.get("value")
        rows.append(obj)
    return rows


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


def upload_table(table_name, sql_template, columns, local_conn, where_clause="", where_args=None):
    """Upload rows from a table using concurrent HTTP connections."""
    query = f'SELECT * FROM {table_name}'
    count_query = f'SELECT COUNT(*) FROM {table_name}'
    if where_clause:
        query += f' WHERE {where_clause}'
        count_query += f' WHERE {where_clause}'

    total = local_conn.execute(count_query, where_args or []).fetchone()[0]
    if total == 0:
        print(f"\n{table_name}: 0 new rows, skipping.")
        return

    print(f"\nUploading {total:,} {table_name}...")

    cursor = local_conn.execute(query, where_args or [])
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


def rebuild_fts5():
    """Rebuild the FTS5 full-text search index on Turso."""
    print("\nRebuilding FTS5 full-text search index...")
    try:
        execute('DROP TABLE IF EXISTS transcript_fts')
    except Exception as e:
        print(f"  Warning dropping FTS table: {e}")
    execute('''CREATE VIRTUAL TABLE transcript_fts USING fts5(
        text,
        content=transcript_segments,
        content_rowid=rowid
    )''')
    execute("INSERT INTO transcript_fts(transcript_fts) VALUES('rebuild')")
    print("  FTS5 index rebuilt.")


def ensure_tables():
    """Create tables and indexes if they don't exist."""
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
    execute('CREATE INDEX IF NOT EXISTS idx_segments_video ON transcript_segments(video_id)')
    execute('CREATE INDEX IF NOT EXISTS idx_bible_book ON bible_references(book)')
    execute('CREATE INDEX IF NOT EXISTS idx_bible_chapter ON bible_references(book, chapter)')
    execute('CREATE INDEX IF NOT EXISTS idx_bible_video ON bible_references(video_id)')
    execute('CREATE INDEX IF NOT EXISTS idx_topic ON theological_topics(topic)')
    execute('CREATE INDEX IF NOT EXISTS idx_topic_video ON theological_topics(video_id)')


def upload_incremental():
    """Only upload videos that don't already exist in Turso."""
    local = sqlite3.connect(LOCAL_DB)
    local.row_factory = sqlite3.Row
    start_total = time.time()

    # Ensure tables exist on Turso
    print("Ensuring tables exist...")
    ensure_tables()

    # Get existing video_ids from Turso
    print("Querying Turso for existing videos...")
    remote_rows = query_rows('SELECT video_id FROM videos')
    remote_ids = set(r['video_id'] for r in remote_rows)
    print(f"  Turso has {len(remote_ids):,} videos")

    # Get local video_ids
    local_ids = set(r['video_id'] for r in local.execute('SELECT video_id FROM videos').fetchall())
    print(f"  Local has {len(local_ids):,} videos")

    # Find new video_ids
    new_ids = local_ids - remote_ids
    if not new_ids:
        print("\n✅ Turso is already up to date! No new videos to sync.")
        local.close()
        return

    print(f"\n  {len(new_ids)} new video(s) to upload")

    # Build placeholders for WHERE clause
    placeholders = ','.join('?' for _ in new_ids)
    new_ids_list = list(new_ids)

    upload_table('videos',
        'INSERT OR REPLACE INTO videos (video_id, title, duration, url, date_published) VALUES (?, ?, ?, ?, ?)',
        ['video_id', 'title', 'duration', 'url', 'date_published'],
        local,
        where_clause=f'video_id IN ({placeholders})',
        where_args=new_ids_list)

    upload_table('transcript_segments',
        'INSERT OR REPLACE INTO transcript_segments (id, video_id, start_time, end_time, text, vimeo_url) VALUES (?, ?, ?, ?, ?, ?)',
        ['id', 'video_id', 'start_time', 'end_time', 'text', 'vimeo_url'],
        local,
        where_clause=f'video_id IN ({placeholders})',
        where_args=new_ids_list)

    upload_table('bible_references',
        'INSERT OR REPLACE INTO bible_references (id, video_id, book, chapter, verse_start, verse_end, start_time, end_time, context) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        ['id', 'video_id', 'book', 'chapter', 'verse_start', 'verse_end', 'start_time', 'end_time', 'context'],
        local,
        where_clause=f'video_id IN ({placeholders})',
        where_args=new_ids_list)

    upload_table('theological_topics',
        'INSERT OR REPLACE INTO theological_topics (id, video_id, topic, keyword_matched, start_time, end_time, context) VALUES (?, ?, ?, ?, ?, ?, ?)',
        ['id', 'video_id', 'topic', 'keyword_matched', 'start_time', 'end_time', 'context'],
        local,
        where_clause=f'video_id IN ({placeholders})',
        where_args=new_ids_list)

    local.close()

    # Rebuild FTS5 to include new content
    rebuild_fts5()

    elapsed = time.time() - start_total
    print(f"\nIncremental sync complete! {len(new_ids)} new video(s) in {elapsed:.1f}s ({elapsed/60:.1f} min)")


def upload_full():
    """Drop everything and re-upload from scratch."""
    local = sqlite3.connect(LOCAL_DB)
    local.row_factory = sqlite3.Row
    start_total = time.time()

    print("FULL RE-UPLOAD: Dropping existing tables...")
    for table in ['transcript_fts', 'theological_topics', 'bible_references', 'transcript_segments', 'videos']:
        try:
            execute(f'DROP TABLE IF EXISTS {table}')
        except Exception as e:
            print(f"  Warning dropping {table}: {e}")

    print("Creating tables...")
    ensure_tables()

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

    rebuild_fts5()

    elapsed = time.time() - start_total
    print(f"\nFull upload complete! Total time: {elapsed:.1f}s ({elapsed/60:.1f} min)")


if __name__ == '__main__':
    if '--full' in sys.argv:
        upload_full()
    else:
        upload_incremental()
