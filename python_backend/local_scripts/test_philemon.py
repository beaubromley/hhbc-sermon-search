# test_philemon.py
import sqlite3
from pathlib import Path

DATABASE_PATH = Path('data/database/transcripts.db')
conn = sqlite3.connect(DATABASE_PATH)
c = conn.cursor()

# Check if Philemon exists in database
c.execute("SELECT COUNT(*) FROM bible_references WHERE book = 'Philemon'")
count = c.fetchone()[0]
print(f"Philemon references in database: {count}")

# Show some examples
c.execute("""
    SELECT br.book, br.chapter, br.verse_start, v.title 
    FROM bible_references br
    JOIN videos v ON br.video_id = v.video_id
    WHERE br.book = 'Philemon'
    LIMIT 10
""")

print("\nSample Philemon references:")
for row in c.fetchall():
    print(f"  {row}")

conn.close()
