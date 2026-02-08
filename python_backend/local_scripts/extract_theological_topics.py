# extract_theological_topics.py
import sqlite3
import re
from pathlib import Path
from collections import defaultdict

DATABASE_PATH = Path('data/database/transcripts.db')

# Define theological topics with keywords
THEOLOGICAL_TOPICS = {
    'Salvation': [
        'salvation', 'saved', 'born again', 'redemption', 'redeemed', 
        'justification', 'justified', 'reconciliation', 'atonement'
    ],
    'Faith': [
        'faith', 'believe', 'belief', 'trust', 'trusting in god',
        'faithful', 'faithfulness'
    ],
    'Prayer': [
        'prayer', 'pray', 'praying', 'intercession', 'petition',
        'supplication', 'prayed'
    ],
    'Grace': [
        'grace', 'gracious', 'mercy', 'merciful', 'compassion',
        'compassionate', 'unmerited favor'
    ],
    'Love': [
        'love', 'loving', 'beloved', 'charity', 'agape',
        'love one another', 'god\'s love'
    ],
    'Sin': [
        'sin', 'sinful', 'transgression', 'iniquity', 'wickedness',
        'trespass', 'fall short', 'sinned'
    ],
    'Repentance': [
        'repent', 'repentance', 'turn from sin', 'confession',
        'confess', 'godly sorrow'
    ],
    'Forgiveness': [
        'forgive', 'forgiveness', 'pardon', 'pardoned',
        'sins forgiven', 'forgiving'
    ],
    'Holy Spirit': [
        'holy spirit', 'spirit of god', 'comforter', 'helper',
        'advocate', 'paraclete', 'spirit'
    ],
    'Jesus Christ': [
        'jesus', 'christ', 'messiah', 'savior', 'lord jesus',
        'son of god', 'lamb of god', 'redeemer'
    ],
    'God the Father': [
        'father', 'heavenly father', 'god the father', 'abba',
        'almighty', 'creator'
    ],
    'Trinity': [
        'trinity', 'triune', 'three in one', 'godhead'
    ],
    'Worship': [
        'worship', 'praise', 'adoration', 'glorify', 'exalt',
        'magnify', 'honor god'
    ],
    'Church': [
        'church', 'body of christ', 'bride of christ', 'fellowship',
        'congregation', 'assembly', 'ekklesia'
    ],
    'Discipleship': [
        'disciple', 'discipleship', 'follow jesus', 'follower',
        'spiritual growth', 'sanctification'
    ],
    'Evangelism': [
        'evangelism', 'witness', 'testimony', 'gospel', 'good news',
        'share your faith', 'great commission'
    ],
    'Baptism': [
        'baptism', 'baptize', 'baptized', 'immersion', 'water baptism'
    ],
    'Communion': [
        'communion', 'lord\'s supper', 'eucharist', 'breaking bread',
        'body and blood'
    ],
    'Heaven': [
        'heaven', 'eternal life', 'paradise', 'glory', 'heavenly',
        'kingdom of heaven'
    ],
    'Hell': [
        'hell', 'damnation', 'eternal punishment', 'lake of fire',
        'gehenna', 'hades'
    ],
    'Second Coming': [
        'second coming', 'return of christ', 'rapture', 'end times',
        'last days', 'parousia', 'coming again'
    ],
    'Resurrection': [
        'resurrection', 'risen', 'raised from the dead', 'easter',
        'empty tomb', 'he is risen'
    ],
    'Cross': [
        'cross', 'crucifixion', 'crucified', 'calvary', 'golgotha',
        'died for our sins'
    ],
    'Hope': [
        'hope', 'hopeful', 'living hope', 'blessed hope',
        'hope in christ'
    ],
    'Joy': [
        'joy', 'joyful', 'rejoice', 'rejoicing', 'gladness',
        'happiness in christ'
    ],
    'Peace': [
        'peace', 'peaceful', 'peace of god', 'shalom',
        'peace that passes understanding'
    ],
    'Suffering': [
        'suffering', 'trials', 'tribulation', 'persecution',
        'affliction', 'hardship', 'pain'
    ],
    'Obedience': [
        'obedience', 'obey', 'obedient', 'submission', 'submit',
        'follow god\'s commands'
    ],
    'Holiness': [
        'holiness', 'holy', 'sanctification', 'sanctified',
        'set apart', 'righteousness', 'righteous'
    ],
    'Covenant': [
        'covenant', 'promise', 'testament', 'agreement',
        'new covenant', 'old covenant'
    ],
    'Kingdom of God': [
        'kingdom of god', 'kingdom of heaven', 'kingdom',
        'reign of god', 'god\'s kingdom'
    ],
    'Prophecy': [
        'prophecy', 'prophetic', 'prophet', 'foretold',
        'fulfillment', 'messianic prophecy'
    ],
    'Miracles': [
        'miracle', 'miraculous', 'signs and wonders', 'healing',
        'supernatural', 'divine intervention'
    ],
    'Stewardship': [
        'stewardship', 'tithe', 'tithing', 'giving', 'generosity',
        'offering', 'financial stewardship'
    ],
    'Service': [
        'service', 'serve', 'servant', 'ministry', 'minister',
        'serving others', 'good works'
    ],
    'Family': [
        'family', 'marriage', 'parenting', 'children', 'husband',
        'wife', 'family values'
    ],
    'Wisdom': [
        'wisdom', 'wise', 'discernment', 'understanding',
        'knowledge', 'prudence'
    ],
    'Hypostatic Union': [
        'hypostatic union', 'fully god and fully man', 'divine nature',
        'human nature', 'two natures', 'god and man', 'deity of christ',
        'humanity of christ', 'incarnation'
    ],
    'Predestination': [
        'predestination', 'predestined', 'election', 'elect', 'chosen',
        'foreknowledge', 'foreordained', 'sovereignty of god',
        'divine election', 'unconditional election'
    ],
    'Spiritual Warfare': [
        'spiritual warfare', 'spiritual battle', 'armor of god',
        'principalities and powers', 'demons', 'demonic', 'satan',
        'devil', 'enemy', 'spiritual attack', 'strongholds',
        'bind and loose', 'spiritual authority'
    ],
    'Church Leadership': [
        'apostle', 'apostles', 'elder', 'elders', 'deacon', 'deacons',
        'pastor', 'bishop', 'overseer', 'shepherd', 'church leadership',
        'pastoral', 'ministry leadership', 'church government'
    ],
    'Marriage': [
        'marriage', 'married', 'husband and wife', 'matrimony',
        'wedding', 'marital', 'spouse', 'covenant marriage',
        'biblical marriage', 'one flesh'
    ],
    'Divorce': [
        'divorce', 'divorced', 'separation', 'remarriage',
        'marital unfaithfulness', 'adultery', 'broken marriage'
    ],
    'Spiritual Gifts': [
        'spiritual gifts', 'gifts of the spirit', 'prophecy', 'tongues',
        'interpretation', 'healing', 'miracles', 'word of knowledge',
        'word of wisdom', 'discernment', 'faith gift', 'helps',
        'administration', 'teaching gift', 'exhortation', 'giving',
        'leadership gift', 'mercy', 'apostleship', 'evangelism'
    ],
}

def create_topics_table():
    """Create table for theological topics"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS theological_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            topic TEXT,
            keyword_matched TEXT,
            start_time REAL,
            end_time REAL,
            context TEXT,
            FOREIGN KEY (video_id) REFERENCES videos (video_id)
        )
    ''')
    
    # Create indexes
    c.execute('CREATE INDEX IF NOT EXISTS idx_topic ON theological_topics(topic)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_topic_video ON theological_topics(video_id)')
    
    conn.commit()
    conn.close()
    print("✅ Theological topics table created")

def extract_topics_from_text(text):
    """Extract theological topics from text"""
    found_topics = []
    text_lower = text.lower()
    
    for topic, keywords in THEOLOGICAL_TOPICS.items():
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_topics.append({
                    'topic': topic,
                    'keyword': keyword
                })
                break  # Only count each topic once per segment
    
    return found_topics

def process_transcripts_for_topics():
    """Process all transcripts and extract theological topics"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    # Clear existing topic data
    c.execute('DELETE FROM theological_topics')
    conn.commit()
    
    # Get all transcript segments
    c.execute('SELECT video_id, start_time, end_time, text FROM transcript_segments')
    segments = c.fetchall()
    
    print(f"Processing {len(segments):,} transcript segments...")
    
    topics_found = 0
    videos_processed = set()
    
    for video_id, start_time, end_time, text in segments:
        videos_processed.add(video_id)
        
        # Extract topics from this segment
        topics = extract_topics_from_text(text)
        
        for topic_data in topics:
            c.execute('''
                INSERT INTO theological_topics 
                (video_id, topic, keyword_matched, start_time, end_time, context)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                topic_data['topic'],
                topic_data['keyword'],
                start_time,
                end_time,
                text[:200]
            ))
            topics_found += 1
        
        # Commit every 1000 segments
        if len(videos_processed) % 100 == 0:
            conn.commit()
            print(f"  Processed {len(videos_processed)} videos, found {topics_found:,} topic mentions...")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Complete!")
    print(f"   Videos processed: {len(videos_processed)}")
    print(f"   Topic mentions found: {topics_found:,}")

def show_topic_summary():
    """Show summary of topics found"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    print("\n" + "=" * 60)
    print("TOPIC SUMMARY")
    print("=" * 60)
    
    # Count by topic
    c.execute('''
        SELECT topic, COUNT(*) as count, COUNT(DISTINCT video_id) as video_count
        FROM theological_topics 
        GROUP BY topic 
        ORDER BY count DESC
    ''')
    
    print("\nTop topics mentioned:")
    print(f"{'Topic':<25} {'Mentions':<12} {'Videos'}")
    print("-" * 60)
    for topic, count, video_count in c.fetchall():
        print(f"{topic:<25} {count:<12} {video_count}")
    
    conn.close()

def test_topic_extraction():
    """Test topic extraction on sample texts"""
    test_texts = [
        "We are saved by grace through faith",
        "Prayer is essential to our walk with God",
        "Jesus Christ died on the cross for our sins",
        "The Holy Spirit guides us into all truth",
        "Repentance leads to forgiveness and salvation"
    ]
    
    print("Testing topic extraction:")
    print("=" * 60)
    
    for text in test_texts:
        topics = extract_topics_from_text(text)
        print(f"\nText: {text}")
        print(f"Topics found: {[t['topic'] for t in topics]}")

def main():
    print("=" * 60)
    print("THEOLOGICAL TOPIC EXTRACTOR")
    print("=" * 60)
    
    # Test first
    print("\n1. Testing topic extraction...")
    test_topic_extraction()
    
    proceed = input("\nLooks good? Proceed with full extraction? (y/n): ").lower()
    if proceed != 'y':
        print("Cancelled")
        return
    
    # Create table
    print("\n2. Creating database table...")
    create_topics_table()
    
    # Process transcripts
    print("\n3. Processing all transcripts...")
    process_transcripts_for_topics()
    
    # Show summary
    print("\n4. Generating summary...")
    show_topic_summary()

if __name__ == "__main__":
    import sys
    
    # Check for --incremental flag
    if '--incremental' in sys.argv:
        print("Running in INCREMENTAL mode (new videos only)")
        
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        
        # Get videos that already have topics extracted
        c.execute('SELECT DISTINCT video_id FROM theological_topics')
        processed_video_ids = set(row[0] for row in c.fetchall())
        
        # Get all videos in database
        c.execute('SELECT DISTINCT video_id FROM transcript_segments')
        all_video_ids = set(row[0] for row in c.fetchall())
        
        # Find videos that need processing
        videos_to_process = all_video_ids - processed_video_ids
        
        if not videos_to_process:
            print("✅ All videos already have theological topics extracted!")
            conn.close()
        else:
            print(f"Processing {len(videos_to_process)} new videos...")
            print(f"(Skipping {len(processed_video_ids)} already processed)")
            
            topics_found = 0
            videos_processed = 0
            
            for video_id in videos_to_process:
                # Get segments for this video
                c.execute('SELECT start_time, end_time, text FROM transcript_segments WHERE video_id = ?', (video_id,))
                segments = c.fetchall()
                
                for start_time, end_time, text in segments:
                    topics = extract_topics_from_text(text)
                    
                    for topic_data in topics:
                        c.execute('''
                            INSERT INTO theological_topics 
                            (video_id, topic, keyword_matched, start_time, end_time, context)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            video_id,
                            topic_data['topic'],
                            topic_data['keyword'],
                            start_time,
                            end_time,
                            text[:200]
                        ))
                        topics_found += 1
                
                videos_processed += 1
                
                if videos_processed % 10 == 0:
                    conn.commit()
                    print(f"  Processed {videos_processed}/{len(videos_to_process)} videos, found {topics_found} topics...")
            
            conn.commit()
            conn.close()
            
            print(f"\n✅ Complete!")
            print(f"   New videos processed: {videos_processed}")
            print(f"   Topic mentions found: {topics_found}")
    else:
        # Run full extraction with prompts
        main()
