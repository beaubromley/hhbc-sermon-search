import sqlite3
import json
import gzip
from pathlib import Path
from collections import defaultdict

# Paths
BACKEND_DIR = Path(__file__).parent
DATA_DIR = BACKEND_DIR / 'data'
DATABASE_PATH = DATA_DIR / 'database' / 'transcripts.db'
FRONTEND_DATA_DIR = BACKEND_DIR.parent / 'frontend' / 'public' / 'data'

def export_search_index():
    """Export a pre-built search index for fast client-side search"""
    print("Creating search index...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    # Get all transcript segments with video info
    c.execute('''
        SELECT 
            ts.video_id,
            v.title,
            v.date_published,
            ts.start_time,
            ts.text,
            ts.vimeo_url
        FROM transcript_segments ts
        JOIN videos v ON ts.video_id = v.video_id
        ORDER BY ts.video_id, ts.start_time
    ''')
    
    rows = c.fetchall()
    
    # Build inverted index: word -> list of segment IDs
    word_index = defaultdict(set)
    segments = []
    
    for idx, (video_id, title, date, start_time, text, url) in enumerate(rows):
        # Store segment info
        segments.append({
            'i': idx,
            'v': video_id,
            't': title,
            'd': date[:10],
            's': start_time,
            'x': text[:300],
            'u': url
        })
        
        # Index words
        words = text.lower().split()
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum() or c == "'")
            if len(clean_word) >= 2:
                word_index[clean_word].add(idx)
    
    # Convert sets to lists
    word_index_json = {word: list(indices) for word, indices in word_index.items()}
    
    print(f"  Indexed {len(segments):,} transcript segments")
    print(f"  Created index with {len(word_index_json):,} unique words")
    
    # Export segments (compressed)
    segments_file = FRONTEND_DATA_DIR / 'search_segments.json'
    segments_gz = FRONTEND_DATA_DIR / 'search_segments.json.gz'
    
    # Write JSON
    with open(segments_file, 'w', encoding='utf-8') as f:
        json.dump(segments, f, separators=(',', ':'))
    
    # Compress
    with open(segments_file, 'rb') as f_in:
        with gzip.open(segments_gz, 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())
    
    segments_size = segments_file.stat().st_size / 1024 / 1024
    segments_gz_size = segments_gz.stat().st_size / 1024 / 1024
    
    print(f"  ✅ Segments: {segments_size:.2f} MB (uncompressed)")
    print(f"  ✅ Segments: {segments_gz_size:.2f} MB (compressed, {(1 - segments_gz_size/segments_size)*100:.1f}% smaller)")
    
    # Export word index (compressed)
    index_file = FRONTEND_DATA_DIR / 'search_index.json'
    index_gz = FRONTEND_DATA_DIR / 'search_index.json.gz'
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(word_index_json, f, separators=(',', ':'))
    
    with open(index_file, 'rb') as f_in:
        with gzip.open(index_gz, 'wb', compresslevel=9) as f_out:
            f_out.write(f_in.read())
    
    index_size = index_file.stat().st_size / 1024 / 1024
    index_gz_size = index_gz.stat().st_size / 1024 / 1024
    
    print(f"  ✅ Index: {index_size:.2f} MB (uncompressed)")
    print(f"  ✅ Index: {index_gz_size:.2f} MB (compressed, {(1 - index_gz_size/index_size)*100:.1f}% smaller)")
    
    total_compressed = segments_gz_size + index_gz_size
    print(f"\n  📦 Total compressed: {total_compressed:.2f} MB")
    
    conn.close()
    
    return len(segments)

if __name__ == "__main__":
    print("=" * 60)
    print("CREATING SEARCH INDEX FOR JAVASCRIPT FRONTEND")
    print("=" * 60)
    
    if not DATABASE_PATH.exists():
        print(f"\n❌ ERROR: Database not found at {DATABASE_PATH}")
        print("Run update_database.py first.")
        exit(1)
    
    total = export_search_index()
    
    print("\n" + "=" * 60)
    print("SEARCH INDEX EXPORT COMPLETE!")
    print("=" * 60)
    print(f"\n✅ Indexed {total:,} transcript segments")
    print("\nCompressed files ready for Vue.js app:")
    print("  - search_segments.json.gz")
    print("  - search_index.json.gz")
