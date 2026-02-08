# find_missing_transcripts.py
import json
from pathlib import Path

TRANSCRIPT_DIR = Path('data/transcripts')
video_data_path = TRANSCRIPT_DIR / 'video_data.json'

with open(video_data_path, 'r', encoding='utf-8') as f:
    videos = json.load(f)

print("Videos WITHOUT transcripts (first 20):")
print("=" * 80)

count = 0
for video in videos:
    transcript_file = TRANSCRIPT_DIR / f"{video['id']}_en-x-autogen.vtt"
    if not transcript_file.exists():
        count += 1
        if count <= 20:
            print(f"{count}. ID: {video['id']}")
            print(f"   Title: {video['title']}")
            print(f"   Date: {video['date'][:10]}")
            print(f"   URL: {video['url']}")
            print("-" * 80)

print(f"\nTotal videos without transcripts: {count}")
