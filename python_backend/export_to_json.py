# export_to_json.py
# Exports speakers.json for the Vue.js frontend.
# All other data (videos, bible refs, topics, transcripts) is served from Turso.
import json
import re
from pathlib import Path

# Paths
BACKEND_DIR = Path(__file__).parent
DATA_DIR = BACKEND_DIR / 'data'
TRANSCRIPT_DIR = DATA_DIR / 'transcripts'
FRONTEND_DATA_DIR = BACKEND_DIR.parent / 'frontend' / 'public' / 'data'

# Ensure frontend data directory exists
FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Canonical speaker name mappings (typos, prefixes, suffixes -> official name)
NAME_NORMALIZATIONS = {
    # Official spellings
    'John Wohlegemuth': 'John Wohlgemuth',
    'Alan Rice': 'Allen Rice',
    # Dr. prefixes -> plain name (guest speakers keep title via Dr. Tedd Tripp etc.)
    'Dr. Allen Rice': 'Allen Rice',
    'Dr. Mark Wood': 'Mark Wood',
    'Dr. Brad Farris': 'Brad Farris',
    'Dr. Carl Trueman': 'Carl Trueman',
    'Dr. Daniel Akin': 'Daniel Akin',
    'Dr. David Sills': 'David Sills',
    'Dr. Matthew Emerson': 'Matthew Emerson',
    'Dr. T.R. Lewis': 'T.R. Lewis',
    'T. R. Lewis': 'T.R. Lewis',
    'Johnny R. Moore': 'Johnny Moore',
    'Pastor Diomodes': 'Pastor Diomedes',
    'Steve Murdoch': 'Steve Murdock',
    # Auto-transcript mishearings
    'Phil Ali': 'Phil Sallee',
    'Dan Lee': 'Dan Leaphart',
    'Kelly Wehen': 'Kelly Wehunt',
    'Kelly Weehett': 'Kelly Wehunt',
    'John Lead': 'John Leaphart',
    'Craig Mc': 'Craig McClain',
}


def normalize_speaker(name):
    """Clean up and normalize a speaker name."""
    if not name or name == 'Unknown':
        return 'Unknown'

    name = name.strip()

    # Remove trailing date info: "Chris Newkirk Date: February 20th, 2011 at ..."
    if ' Date:' in name:
        name = name[:name.index(' Date:')].strip()

    # Remove trailing "at Henderson Hills..." or similar
    if ' at Henderson' in name:
        name = name[:name.index(' at Henderson')].strip()

    # Remove trailing "www." or "hendersonhills"
    if 'hendersonhills' in name.lower() or 'www.' in name:
        for marker in ['hendersonhills', 'www.']:
            idx = name.lower().find(marker)
            if idx > 0:
                name = name[:idx].strip().rstrip('.')

    # Apply explicit normalizations
    if name in NAME_NORMALIZATIONS:
        name = NAME_NORMALIZATIONS[name]

    return name.strip() if name.strip() else 'Unknown'


def extract_speaker_from_description(desc):
    """Extract speaker from video description using known patterns."""
    if not desc:
        return None

    # Pattern 1: "Speaker: Name"
    if 'Speaker:' in desc:
        start = desc.index('Speaker:') + len('Speaker:')
        raw = desc[start:].strip().split('\n')[0].strip()
        if raw:
            return raw

    # Pattern 2: "Presented by Name on Date" or "Presented by Name, ..."
    if 'Presented by' in desc:
        start = desc.index('Presented by') + len('Presented by')
        rest = desc[start:].strip()
        # Try " on " first (most common)
        on_idx = rest.find(' on ')
        comma_idx = rest.find(',')
        newline_idx = rest.find('\n')
        # Pick the earliest delimiter
        candidates = []
        if on_idx > 0:
            candidates.append(on_idx)
        if comma_idx > 0:
            candidates.append(comma_idx)
        if newline_idx > 0:
            candidates.append(newline_idx)
        if candidates:
            end = min(candidates)
            speaker = rest[:end].strip()
        else:
            speaker = rest.strip()
        if speaker:
            return speaker

    # Pattern 3: "Name preaches ..."
    if 'preaches' in desc.lower():
        speaker = desc.split('preaches')[0].strip()
        if speaker:
            return speaker

    return None


def get_vtt_text_first_n_seconds(vtt_path, seconds=90):
    """Read a VTT file and return concatenated text from the first N seconds."""
    try:
        with open(vtt_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return ''

    parts = []
    for match in re.finditer(r'(\d{2}):(\d{2}):(\d{2})\.\d+ --> .+\n(.+)', content):
        h, m, s, text = match.groups()
        time_sec = int(h) * 3600 + int(m) * 60 + int(s)
        if time_sec > seconds:
            break
        parts.append(text)
    return ' '.join(parts)


def extract_speaker_from_transcript(video_id):
    """Try to detect speaker name from the first 90 seconds of transcript."""
    vtt_path = TRANSCRIPT_DIR / f'{video_id}_en-x-autogen.vtt'
    if not vtt_path.exists():
        return None

    text = get_vtt_text_first_n_seconds(vtt_path, 90)
    if not text:
        return None

    # Patterns that reliably indicate a speaker name (ordered by confidence)
    patterns = [
        r"[Mm]y name is ([A-Z][a-z]+ [A-Z][a-z]+)",
        r"[Mm]y name'?s ([A-Z][a-z]+ [A-Z][a-z]+)",
        r"[Pp]lease welcome ([A-Z][a-z]+ [A-Z][a-z]+)",
    ]

    for pat in patterns:
        m = re.search(pat, text)
        if m:
            name = m.group(1)
            # Require last name to be at least 3 chars (avoid truncated names)
            parts = name.split()
            if len(parts) == 2 and len(parts[1]) >= 3:
                return name

    return None


def export_speakers():
    """Export speaker information from video_data.json"""
    print("Exporting speaker information...")

    video_data_path = DATA_DIR / 'transcripts' / 'video_data.json'

    if not video_data_path.exists():
        print("  video_data.json not found, skipping speaker export")
        return 0

    with open(video_data_path, 'r', encoding='utf-8') as f:
        videos = json.load(f)

    speakers = {}
    from_desc = 0
    from_transcript = 0
    unknown = 0

    for video in videos:
        vid = str(video['id'])
        desc = video.get('description', '')

        # Try description first
        speaker = extract_speaker_from_description(desc)

        # If no speaker from description, try transcript
        if not speaker:
            speaker = extract_speaker_from_transcript(vid)
            if speaker:
                from_transcript += 1
        else:
            from_desc += 1

        # Normalize the name
        speaker = normalize_speaker(speaker) if speaker else 'Unknown'

        if speaker == 'Unknown':
            unknown += 1

        speakers[vid] = speaker

    output_file = FRONTEND_DATA_DIR / 'speakers.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(speakers, f, indent=2, ensure_ascii=False)

    total = len(speakers)
    known = total - unknown
    print(f"  Exported speaker info for {total} videos to {output_file}")
    print(f"  From description: {from_desc}")
    print(f"  From transcript:  {from_transcript}")
    print(f"  Known: {known}/{total} ({100 * known // total}%)")
    print(f"  Unknown: {unknown}")
    return total


def main():
    print("=" * 60)
    print("EXPORTING SPEAKERS.JSON FOR FRONTEND")
    print("=" * 60)

    speaker_count = export_speakers()

    print(f"\nExport complete! {speaker_count} speakers written.")


if __name__ == "__main__":
    main()
