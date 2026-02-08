# export_to_json.py
import sqlite3
import json
import gzip
import shutil
from pathlib import Path
from datetime import datetime

# Paths
BACKEND_DIR = Path(__file__).parent
DATA_DIR = BACKEND_DIR / 'data'
DATABASE_PATH = DATA_DIR / 'database' / 'transcripts.db'
FRONTEND_DATA_DIR = BACKEND_DIR.parent / 'frontend' / 'public' / 'data'

# Ensure frontend data directory exists
FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

def export_videos():
    """Export videos table to JSON"""
    print("Exporting videos...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    c.execute('SELECT video_id, title, duration, url, date_published FROM videos ORDER BY date_published DESC')
    rows = c.fetchall()
    
    videos = []
    for video_id, title, duration, url, date_published in rows:
        videos.append({
            'id': video_id,
            'title': title,
            'duration': duration,
            'url': url,
            'date': date_published
        })
    
    conn.close()
    
    output_file = FRONTEND_DATA_DIR / 'videos.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Exported {len(videos)} videos to {output_file}")
    return len(videos)

def export_bible_references():
    """Export Bible references"""
    print("Exporting Bible references...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT video_id, book, chapter, verse_start, verse_end, start_time, end_time, context
        FROM bible_references
        ORDER BY video_id, book, chapter, verse_start
    ''')
    rows = c.fetchall()
    
    bible_refs = []
    for video_id, book, chapter, verse_start, verse_end, start_time, end_time, context in rows:
        bible_refs.append({
            'video_id': video_id,
            'book': book,
            'chapter': chapter,
            'verse_start': verse_start,
            'verse_end': verse_end,
            'start_time': start_time,
            'end_time': end_time,
            'context': context
        })
    
    conn.close()
    
    output_file = FRONTEND_DATA_DIR / 'bible_references.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(bible_refs, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Exported {len(bible_refs):,} Bible references to {output_file}")
    return len(bible_refs)

def export_theological_topics():
    """Export theological topics"""
    print("Exporting theological topics...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT video_id, topic, keyword_matched, start_time, end_time, context
        FROM theological_topics
        ORDER BY video_id, topic
    ''')
    rows = c.fetchall()
    
    topics = []
    for video_id, topic, keyword, start_time, end_time, context in rows:
        topics.append({
            'video_id': video_id,
            'topic': topic,
            'keyword': keyword,
            'start_time': start_time,
            'end_time': end_time,
            'context': context
        })
    
    conn.close()
    
    output_file = FRONTEND_DATA_DIR / 'theological_topics.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(topics, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Exported {len(topics):,} theological topic mentions to {output_file}")
    return len(topics)

def export_speakers():
    """Export speaker information from video_data.json"""
    print("Exporting speaker information...")
    
    video_data_path = DATA_DIR / 'transcripts' / 'video_data.json'
    
    if not video_data_path.exists():
        print("  ⚠️  video_data.json not found, skipping speaker export")
        return 0
    
    with open(video_data_path, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    # Extract speakers
    speakers = {}
    for video in videos:
        desc = video.get('description', '')
        speaker = "Unknown"
        
        if desc and 'Speaker:' in desc:
            try:
                start = desc.index('Speaker:') + len('Speaker:')
                speaker = desc[start:].strip().split('\n')[0].strip()
            except:
                pass
        elif desc and 'Presented by' in desc:
            try:
                start = desc.index('Presented by') + len('Presented by')
                end = desc.index(' on ', start)
                speaker = desc[start:end].strip()
            except:
                pass
        elif desc and 'preaches' in desc.lower():
            try:
                speaker = desc.split('preaches')[0].strip()
            except:
                pass
        
        speakers[video['id']] = speaker
    
    output_file = FRONTEND_DATA_DIR / 'speakers.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(speakers, f, indent=2, ensure_ascii=False)
    
    print(f"  ✅ Exported speaker info for {len(speakers)} videos to {output_file}")
    return len(speakers)

def copy_and_compress_database():
    """Copy database to frontend and optionally compress it"""
    print("Copying database to frontend...")
    
    if not DATABASE_PATH.exists():
        print("  ⚠️  Database not found, skipping")
        return
    
    # Copy uncompressed version
    dest_db = FRONTEND_DATA_DIR / 'transcripts.db'
    shutil.copy2(DATABASE_PATH, dest_db)
    
    db_size = dest_db.stat().st_size / (1024 * 1024)
    print(f"  ✅ Copied database: {db_size:.2f} MB")
    
    # Also create compressed version
    print("Creating compressed version...")
    dest_gz = FRONTEND_DATA_DIR / 'transcripts.db.gz'
    
    with open(DATABASE_PATH, 'rb') as f_in:
        with gzip.open(dest_gz, 'wb', compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    gz_size = dest_gz.stat().st_size / (1024 * 1024)
    compression_ratio = (1 - gz_size / db_size) * 100
    
    print(f"  ✅ Created compressed database: {gz_size:.2f} MB ({compression_ratio:.1f}% smaller)")
    print(f"     You can use either transcripts.db or transcripts.db.gz")

def get_file_size_mb(file_path):
    """Get file size in MB"""
    try:
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)
    except:
        return 0

def main():
    print("=" * 60)
    print("EXPORTING DATABASE TO JSON FOR JAVASCRIPT FRONTEND")
    print("=" * 60)
    
    if not DATABASE_PATH.exists():
        print(f"\n❌ ERROR: Database not found at {DATABASE_PATH}")
        print("Run update_and_run.py first to create the database.")
        return
    
    print(f"\nDatabase: {DATABASE_PATH}")
    print(f"Output directory: {FRONTEND_DATA_DIR}")
    print()
    
    # Export all data
    video_count = export_videos()
    bible_count = export_bible_references()
    topic_count = export_theological_topics()
    speaker_count = export_speakers()
    
    # Copy database for sql.js
    copy_and_compress_database()
    
    # Show file sizes
    print("\n" + "=" * 60)
    print("EXPORT COMPLETE!")
    print("=" * 60)
    
    print("\nFile sizes:")
    for file in sorted(FRONTEND_DATA_DIR.glob('*')):
        if file.is_file():
            size_mb = get_file_size_mb(file)
            print(f"  {file.name}: {size_mb:.2f} MB")
    
    total_size = sum(get_file_size_mb(f) for f in FRONTEND_DATA_DIR.glob('*.json'))
    print(f"\nTotal JSON files: {total_size:.2f} MB")
    
    print("\n✅ Data ready for JavaScript frontend!")
    print("\nNext steps:")
    print("1. cd frontend")
    print("2. npm install sql.js (for SQLite in browser)")
    print("3. npm run serve")
    print("4. The app will use transcripts.db for searching")

if __name__ == "__main__":
    main()
