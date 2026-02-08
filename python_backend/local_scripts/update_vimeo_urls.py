# update_vimeo_urls.py
import sqlite3
from pathlib import Path

DATABASE_PATH = Path('data/database/transcripts.db')

def update_urls():
    """Update all vimeo_urls to use player.vimeo.com format"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    print("Updating vimeo_urls to player.vimeo.com format...")
    
    # Update videos table URLs
    print("\nUpdating videos table...")
    c.execute('''
        UPDATE videos
        SET url = 'https://player.vimeo.com/video/' || video_id
    ''')
    
    videos_updated = c.rowcount
    print(f"  Updated {videos_updated:,} video URLs")
    
    # Update transcript_segments table
    print("\nUpdating transcript_segments...")
    c.execute('''
        UPDATE transcript_segments
        SET vimeo_url = 'https://player.vimeo.com/video/' || video_id || '#t=' || CAST(start_time AS INTEGER) || 's'
    ''')
    
    segments_updated = c.rowcount
    print(f"  Updated {segments_updated:,} segments")
    
    # Update transcript_search table
    print("\nUpdating transcript_search...")
    c.execute('''
        DELETE FROM transcript_search
    ''')
    
    c.execute('''
        INSERT INTO transcript_search (video_id, start_time, end_time, text, vimeo_url)
        SELECT video_id, start_time, end_time, text, vimeo_url
        FROM transcript_segments
    ''')
    
    search_updated = c.rowcount
    print(f"  Updated {search_updated:,} search entries")
    
    conn.commit()
    conn.close()
    
    print("\n✅ All URLs updated to player.vimeo.com format!")

if __name__ == "__main__":
    update_urls()
