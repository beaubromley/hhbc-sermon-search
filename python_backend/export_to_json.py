# export_to_json.py
# Exports speakers.json for the Vue.js frontend.
# All other data (videos, bible refs, topics, transcripts) is served from Turso.
import json
from pathlib import Path

# Paths
BACKEND_DIR = Path(__file__).parent
DATA_DIR = BACKEND_DIR / 'data'
FRONTEND_DATA_DIR = BACKEND_DIR.parent / 'frontend' / 'public' / 'data'

# Ensure frontend data directory exists
FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

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

def main():
    print("=" * 60)
    print("EXPORTING SPEAKERS.JSON FOR FRONTEND")
    print("=" * 60)

    speaker_count = export_speakers()

    print(f"\n✅ Export complete! {speaker_count} speakers written.")

if __name__ == "__main__":
    main()
