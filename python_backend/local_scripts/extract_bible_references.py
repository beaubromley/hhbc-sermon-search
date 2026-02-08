# extract_bible_references.py
import sqlite3
import re
from pathlib import Path
import json

DATABASE_PATH = Path('data/database/transcripts.db')
TRANSCRIPT_DIR = Path('data/transcripts')

# Complete list of Bible books with common variations
BIBLE_BOOKS = {
    # Old Testament
    'Genesis': ['Genesis'],
    'Exodus': ['Exodus', 'Ex', 'Exod'],
    'Leviticus': ['Leviticus', 'Le', 'Lv'],
    'Numbers': ['Numbers', 'Num', 'Nu', 'Nm', 'Nb'],
    'Deuteronomy': ['Deuteronomy', 'Deut', 'Dt'],
    'Joshua': ['Joshua', 'Josh', 'Jos'],
    'Judges': ['Judges', 'Judg', 'Jdg'],
    'Ruth': ['Ruth', 'Rth', 'Ru'],
    '1 Samuel': ['1 Samuel', '1 Sam', '1 Sa', 'I Samuel', 'First Samuel'],
    '2 Samuel': ['2 Samuel', '2 Sam', '2 Sa', 'II Samuel', 'Second Samuel'],
    '1 Kings': ['1 Kings', '1 Kgs', '1 Ki', 'I Kings', 'First Kings'],
    '2 Kings': ['2 Kings', '2 Kgs', '2 Ki', 'II Kings', 'Second Kings'],
    '1 Chronicles': ['1 Chronicles', '1 Chron', '1 Chr', 'I Chronicles', 'First Chronicles'],
    '2 Chronicles': ['2 Chronicles', '2 Chron', '2 Chr', 'II Chronicles', 'Second Chronicles'],
    'Ezra': ['Ezra', 'Ezr'],
    'Nehemiah': ['Nehemiah', 'Neh', 'Ne'],
    'Esther': ['Esther', 'Est', 'Es'],
    'Job': ['Job', 'Jb'],
    'Psalms': ['Psalms', 'Psalm', 'Ps', 'Psa', 'Psm'],
    'Proverbs': ['Proverbs', 'Pr', 'Prv'],
    'Ecclesiastes': ['Ecclesiastes', 'Eccles', 'Eccl', 'Ec'],
    'Song of Solomon': ['Song of Solomon', 'Song of Songs'],
    'Isaiah': ['Isaiah'],
    'Jeremiah': ['Jeremiah', 'Jer', 'Je', 'Jr'],
    'Lamentations': ['Lamentations', 'Lam', 'La'],
    'Ezekiel': ['Ezekiel', 'Ezek', 'Eze', 'Ezk'],
    'Daniel': ['Daniel', 'Da', 'Dn'],
    'Hosea': ['Hosea', 'Hos', 'Ho'],
    'Joel': ['Joel', 'Jl'],
    'Amos': ['Amos'],
    'Obadiah': ['Obadiah', 'Obad', 'Ob'],
    'Jonah': ['Jonah', 'Jnh', 'Jon'],
    'Micah': ['Micah', 'Mic', 'Mc'],
    'Nahum': ['Nahum', 'Nah', 'Na'],
    'Habakkuk': ['Habakkuk', 'Hab', 'Hb'],
    'Zephaniah': ['Zephaniah', 'Zeph', 'Zep', 'Zp'],
    'Haggai': ['Haggai', 'Hag', 'Hg'],
    'Zechariah': ['Zechariah', 'Zech', 'Zec', 'Zc'],
    'Malachi': ['Malachi', 'Mal', 'Ml'],
    
    # New Testament
    'Matthew': ['Matthew', 'Mt'],
    'Mark': ['Mark', 'Mrk', 'Mk', 'Mr'],
    'Luke': ['Luke', 'Luk', 'Lk'],
    'John': ['John', 'Jhn', 'Jn'],
    'Acts': ['Acts', 'Ac'],
    'Romans': ['Romans', 'Rom', 'Ro', 'Rm'],
    '1 Corinthians': ['1 Corinthians', '1 Cor', '1 Co', 'I Corinthians', 'First Corinthians'],
    '2 Corinthians': ['2 Corinthians', '2 Cor', '2 Co', 'II Corinthians', 'Second Corinthians'],
    'Galatians': ['Galatians', 'Gal', 'Ga'],
    'Ephesians': ['Ephesians', 'Eph', 'Ephes'],
    'Philippians': ['Philippians', 'Phil', 'Php', 'Pp'],
    'Colossians': ['Colossians', 'Col', 'Co'],
    '1 Thessalonians': ['1 Thessalonians', '1 Thess', '1 Th', 'I Thessalonians', 'First Thessalonians'],
    '2 Thessalonians': ['2 Thessalonians', '2 Thess', '2 Th', 'II Thessalonians', 'Second Thessalonians'],
    '1 Timothy': ['1 Timothy', '1 Tim', '1 Ti', 'I Timothy', 'First Timothy'],
    '2 Timothy': ['2 Timothy', '2 Tim', '2 Ti', 'II Timothy', 'Second Timothy'],
    'Titus': ['Titus', 'Ti'],
    'Philemon': ['Philemon', 'Phlm', 'Phm'],
    'Hebrews': ['Hebrews', 'Heb'],
    'James': ['James', 'Jas', 'Jm'],
    '1 Peter': ['1 Peter', '1 Pet', '1 Pe', '1 Pt', 'I Peter', 'First Peter'],
    '2 Peter': ['2 Peter', '2 Pet', '2 Pe', '2 Pt', 'II Peter', 'Second Peter'],
    '1 John': ['1 John', '1 Jhn', '1 Jn', 'I John', 'First John'],
    '2 John': ['2 John', '2 Jhn', '2 Jn', 'II John', 'Second John'],
    '3 John': ['3 John', '3 Jhn', '3 Jn', 'III John', 'Third John'],
    'Jude': ['Jude', 'Jud'],
    'Revelation': ['Revelation', 'Rev', 'The Revelation', 'Revelations']
}

def create_book_pattern():
    """Create regex pattern for all book names"""
    all_variations = []
    for book, variations in BIBLE_BOOKS.items():
        all_variations.extend(variations)
    
    # Sort by length (longest first) to match "1 Corinthians" before "Corinthians"
    all_variations.sort(key=len, reverse=True)
    
    # Escape special characters and join with |
    pattern = '|'.join(re.escape(v) for v in all_variations)
    return pattern

def normalize_book_name(book_text):
    """Convert any variation to standard book name"""
    for standard_name, variations in BIBLE_BOOKS.items():
        for variation in variations:
            if book_text.lower() == variation.lower():
                return standard_name
    return book_text

def extract_bible_references(text):
    """Extract Bible references from text with validation"""
    references = []
    
    # Build pattern for book names
    book_pattern = create_book_pattern()
    
    # Max chapters and verses per book
    max_chapters = {
        'Genesis': 50, 'Exodus': 40, 'Leviticus': 27, 'Numbers': 36, 'Deuteronomy': 34,
        'Joshua': 24, 'Judges': 21, 'Ruth': 4, '1 Samuel': 31, '2 Samuel': 24,
        '1 Kings': 22, '2 Kings': 25, '1 Chronicles': 29, '2 Chronicles': 36,
        'Ezra': 10, 'Nehemiah': 13, 'Esther': 10, 'Job': 42, 'Psalms': 150,
        'Proverbs': 31, 'Ecclesiastes': 12, 'Song of Solomon': 8, 'Isaiah': 66,
        'Jeremiah': 52, 'Lamentations': 5, 'Ezekiel': 48, 'Daniel': 12,
        'Hosea': 14, 'Joel': 3, 'Amos': 9, 'Obadiah': 1, 'Jonah': 4,
        'Micah': 7, 'Nahum': 3, 'Habakkuk': 3, 'Zephaniah': 3, 'Haggai': 2,
        'Zechariah': 14, 'Malachi': 4,
        'Matthew': 28, 'Mark': 16, 'Luke': 24, 'John': 21, 'Acts': 28,
        'Romans': 16, '1 Corinthians': 16, '2 Corinthians': 13, 'Galatians': 6,
        'Ephesians': 6, 'Philippians': 4, 'Colossians': 4, '1 Thessalonians': 5,
        '2 Thessalonians': 3, '1 Timothy': 6, '2 Timothy': 4, 'Titus': 3,
        'Philemon': 1, 'Hebrews': 13, 'James': 5, '1 Peter': 5, '2 Peter': 3,
        '1 John': 5, '2 John': 1, '3 John': 1, 'Jude': 1, 'Revelation': 22
    }
    
    # Pattern for references like "John 3:16" or "Genesis 1:1-5" or "Psalm 23"
    pattern = rf'\b({book_pattern})[,\s]+(\d+)(?::(\d+)(?:-(\d+))?)?\b'
    
    matches = re.finditer(pattern, text, re.IGNORECASE)
    
    for match in matches:
        book_raw = match.group(1)
        chapter_raw = int(match.group(2))
        verse_start_raw = int(match.group(3)) if match.group(3) else None
        verse_end_raw = int(match.group(4)) if match.group(4) else None
        
        # Normalize book name
        book = normalize_book_name(book_raw)
        
        chapter = chapter_raw
        verse_start = verse_start_raw
        verse_end = verse_end_raw
        
        # Parse combined chapter:verse (like "320" = "3:20" or "1115" = "11:15")
        if verse_start is None and chapter_raw > 150:
            chapter_str = str(chapter_raw)
            max_chap = max_chapters.get(book, 150)
            
            # Try different split points
            possible_splits = []
            for split_pos in range(1, len(chapter_str)):
                potential_chapter = int(chapter_str[:split_pos])
                potential_verse = int(chapter_str[split_pos:])
                
                # Check if this split makes sense
                if potential_chapter <= max_chap and potential_verse <= 176:
                    possible_splits.append((potential_chapter, potential_verse))
            
            # Use the first valid split
            if possible_splits:
                chapter, verse_start = possible_splits[0]
                # Skip year-like numbers
                if chapter_raw >= 1900 and chapter_raw <= 2100:
                    continue
            else:
                # No valid split, skip
                continue
        
        # Validation: Check if chapter is valid for this book
        if book in max_chapters:
            if chapter > max_chapters[book]:
                continue
        else:
            if chapter > 150:
                continue
        
        # Validation: Check if verse numbers are reasonable
        if verse_start:
            max_verse = 176 if book == 'Psalms' else 89
            
            if verse_start > max_verse:
                continue
            
            if verse_end and verse_end > max_verse:
                continue
        
        # Skip years (even if they passed other checks)
        if 1900 <= chapter_raw <= 2100 and verse_start_raw is None:
            continue
        
        references.append({
            'book': book,
            'chapter': chapter,
            'verse_start': verse_start,
            'verse_end': verse_end,
            'raw_text': match.group(0)
        })
    
    # Also catch "chapter X" references
    chapter_pattern = rf'\b({book_pattern})\s+chapter\s+(\d+)\b'
    matches = re.finditer(chapter_pattern, text, re.IGNORECASE)
    
    for match in matches:
        book_raw = match.group(1)
        chapter = int(match.group(2))
        book = normalize_book_name(book_raw)
        
        # Validation
        if book in max_chapters:
            if chapter > max_chapters[book]:
                continue
        elif chapter > 150:
            continue
        
        if 1900 <= chapter <= 2100:
            continue
        
        references.append({
            'book': book,
            'chapter': chapter,
            'verse_start': None,
            'verse_end': None,
            'raw_text': match.group(0)
        })
    
    # Catch standalone book mentions (without chapter numbers)
    standalone_pattern = rf'\b({book_pattern})\b(?!\s*\d)'
    
    matches = re.finditer(standalone_pattern, text, re.IGNORECASE)
    
    for match in matches:
        book_raw = match.group(1)
        book = normalize_book_name(book_raw)
        
        # Skip if we already have a reference for this book in this text
        already_has_chapter = any(
            ref['book'] == book and ref['chapter'] is not None 
            for ref in references
        )
        
        if not already_has_chapter:
            references.append({
                'book': book,
                'chapter': None,
                'verse_start': None,
                'verse_end': None,
                'raw_text': match.group(0)
            })
    
    return references

    
    # Special handling for single-chapter books mentioned without chapter numbers
    single_chapter_books = {
        'Obadiah': ['Obadiah', 'Obad', 'Ob'],
        'Philemon': ['Philemon', 'Phlm', 'Phm'],
        '2 John': ['2 John', '2 Jhn', '2 Jn', 'II John', 'Second John'],
        '3 John': ['3 John', '3 Jhn', '3 Jn', 'III John', 'Third John'],
        'Jude': ['Jude', 'Jud']
    }
    
    for standard_name, variations in single_chapter_books.items():
        for variation in variations:
            # Match book name NOT followed by a number (to avoid duplicates)
            pattern = rf'\b{re.escape(variation)}\b(?!\s+\d)'
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                references.append({
                    'book': standard_name,
                    'chapter': 1,
                    'verse_start': None,
                    'verse_end': None,
                    'raw_text': match.group(0)
                })
    
    return references


def create_bible_references_table():
    """Create table for Bible references"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS bible_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            book TEXT,
            chapter INTEGER,
            verse_start INTEGER,
            verse_end INTEGER,
            start_time REAL,
            end_time REAL,
            context TEXT,
            FOREIGN KEY (video_id) REFERENCES videos (video_id)
        )
    ''')
    
    # Create index for faster searches
    c.execute('CREATE INDEX IF NOT EXISTS idx_bible_book ON bible_references(book)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_bible_chapter ON bible_references(book, chapter)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_bible_video ON bible_references(video_id)')
    
    conn.commit()
    conn.close()
    print("✅ Bible references table created")

def process_transcripts():
    """Process all transcripts and extract Bible references"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    # Clear existing Bible reference data first
    print("Clearing old Bible references...")
    c.execute('DELETE FROM bible_references')
    conn.commit()
    
    # Get all transcript segments
    c.execute('SELECT video_id, start_time, end_time, text FROM transcript_segments')
    segments = c.fetchall()
    
    print(f"Processing {len(segments):,} transcript segments...")
    
    references_found = 0
    videos_processed = set()
    
    for video_id, start_time, end_time, text in segments:
        videos_processed.add(video_id)
        
        # Extract references from this segment
        refs = extract_bible_references(text)
        
        for ref in refs:
            # Insert into database
            c.execute('''
                INSERT INTO bible_references 
                (video_id, book, chapter, verse_start, verse_end, start_time, end_time, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                ref['book'],
                ref['chapter'],
                ref['verse_start'],
                ref['verse_end'],
                start_time,
                end_time,
                text[:200]  # Store context (first 200 chars)
            ))
            references_found += 1
        
        # Commit every 1000 segments
        if len(videos_processed) % 100 == 0:
            conn.commit()
            print(f"  Processed {len(videos_processed)} videos, found {references_found} references...")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Complete!")
    print(f"   Videos processed: {len(videos_processed)}")
    print(f"   Bible references found: {references_found}")

def test_extraction():
    """Test the extraction on sample text"""
    test_texts = [
        "Today we're looking at John 3:16",
        "Turn to Genesis chapter 1",
        "Read Psalm 23:1-6 with me",
        "In 1 Corinthians 13, Paul writes about love",
        "Matthew 5:3-12 are the Beatitudes",
        "Let's go to Romans 8:28"
    ]
    
    print("Testing Bible reference extraction:")
    print("=" * 60)
    
    for text in test_texts:
        refs = extract_bible_references(text)
        print(f"\nText: {text}")
        print(f"Found: {refs}")

def main():
    print("=" * 60)
    print("BIBLE REFERENCE EXTRACTOR")
    print("=" * 60)
    
    # Test first
    print("\n1. Testing extraction patterns...")
    test_extraction()
    
    proceed = input("\nLooks good? Proceed with full extraction? (y/n): ").lower()
    if proceed != 'y':
        print("Cancelled")
        return
    
    # Create table
    print("\n2. Creating database table...")
    create_bible_references_table()
    
    # Process all transcripts
    print("\n3. Processing all transcripts...")
    process_transcripts()
    
    # Show summary
    print("\n4. Summary by book:")
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT book, COUNT(*) as count 
        FROM bible_references 
        GROUP BY book 
        ORDER BY count DESC 
        LIMIT 20
    ''')
    
    print("\nTop 20 most referenced books:")
    for book, count in c.fetchall():
        print(f"  {book}: {count} references")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    # Check for --incremental flag
    if '--incremental' in sys.argv:
        # Just run incremental processing
        print("Running in INCREMENTAL mode (new videos only)")

        create_bible_references_table()

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()

        c.execute('SELECT DISTINCT video_id FROM bible_references')
        processed = set(row[0] for row in c.fetchall())

        c.execute('SELECT DISTINCT video_id FROM transcript_segments')
        all_vids = set(row[0] for row in c.fetchall())

        new_vids = all_vids - processed

        if not new_vids:
            print("✅ All videos already have Bible references extracted!")
            conn.close()
        else:
            print(f"Processing {len(new_vids)} new videos...")
            print(f"(Skipping {len(processed)} already processed)")

            references_found = 0
            videos_processed = 0

            for video_id in new_vids:
                c.execute('SELECT start_time, end_time, text FROM transcript_segments WHERE video_id = ?', (video_id,))
                segments = c.fetchall()

                for start_time, end_time, text in segments:
                    refs = extract_bible_references(text)

                    for ref in refs:
                        c.execute('''
                            INSERT INTO bible_references
                            (video_id, book, chapter, verse_start, verse_end, start_time, end_time, context)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            video_id,
                            ref['book'],
                            ref['chapter'],
                            ref['verse_start'],
                            ref['verse_end'],
                            start_time,
                            end_time,
                            text[:200]
                        ))
                        references_found += 1

                videos_processed += 1

                if videos_processed % 10 == 0:
                    conn.commit()
                    print(f"  Processed {videos_processed}/{len(new_vids)} videos, found {references_found} references...")

            conn.commit()
            conn.close()

            print(f"\n✅ Complete!")
            print(f"   New videos processed: {videos_processed}")
            print(f"   Bible references found: {references_found}")
    else:
        # Run full extraction with prompts
        main()