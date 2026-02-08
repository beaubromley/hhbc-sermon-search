# batch_transcribe.py
import json
from pathlib import Path
import vimeo
import time
import subprocess
import whisper
from datetime import timedelta

TRANSCRIPT_DIR = Path('data/transcripts')
TEMP_DIR = Path('data/temp')
TEMP_DIR.mkdir(exist_ok=True)

# Your working Vimeo credentials
VIMEO_USERNAME = "beaubromley@gmail.com"
VIMEO_PASSWORD = "DC35npLj!!" 

def format_timestamp(seconds):
    """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)"""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def download_vimeo_video(video_id, output_path):
    """Download video from Vimeo using yt-dlp"""
    print(f"  Downloading video {video_id}...")
    
    cmd = [
        'yt-dlp',
        '--username', VIMEO_USERNAME,
        '--password', VIMEO_PASSWORD,
        '-o', str(output_path),
        '--quiet',  # Less verbose
        '--no-warnings',
        f'https://vimeo.com/{video_id}'
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        if output_path.exists():
            return output_path
        return None
    except:
        return None

def extract_audio(video_path, audio_path):
    """Extract audio from video using FFmpeg"""
    print(f"  Extracting audio...")
    
    cmd = [
        'ffmpeg',
        '-i', str(video_path),
        '-vn',
        '-acodec', 'libmp3lame',
        '-ar', '16000',
        '-ac', '1',
        '-y',
        str(audio_path),
        '-loglevel', 'error'  # Only show errors
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return audio_path
    except:
        return None

def transcribe_with_whisper(audio_path, model):
    """Transcribe audio using Whisper"""
    print(f"  Transcribing...")
    
    result = model.transcribe(
        str(audio_path),
        language='en',
        verbose=False  # Don't show progress for batch
    )
    
    return result

def create_vtt_file(segments, output_path):
    """Create VTT file from Whisper segments"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        
        for i, segment in enumerate(segments):
            start = format_timestamp(segment['start'])
            end = format_timestamp(segment['end'])
            text = segment['text'].strip()
            
            f.write(f"{i+1}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
    
    return output_path

def cleanup_temp_files(video_id):
    """Delete temporary video and audio files"""
    video_path = TEMP_DIR / f"{video_id}.mp4"
    audio_path = TEMP_DIR / f"{video_id}.mp3"
    
    if video_path.exists():
        video_path.unlink()
    if audio_path.exists():
        audio_path.unlink()

def main():
    print("=" * 80)
    print("BATCH WHISPER TRANSCRIPTION")
    print("=" * 80)
    
    # Load video data
    video_data_path = TRANSCRIPT_DIR / 'video_data.json'
    with open(video_data_path, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    # Find videos without transcripts
    videos_to_process = []
    for video in videos:
        vtt_file = TRANSCRIPT_DIR / f"{video['id']}_en-x-autogen.vtt"
        if not vtt_file.exists():
            videos_to_process.append(video)
    
    print(f"\nFound {len(videos_to_process)} videos without transcripts")
    print(f"Total videos: {len(videos)}")
    
    if not videos_to_process:
        print("\nAll videos already have transcripts!")
        return
    
    # Ask for confirmation
    print(f"\nThis will process {len(videos_to_process)} videos.")
    print("Estimated time: ~5-10 minutes per video")
    print(f"Total estimated time: {len(videos_to_process) * 7} minutes (~{len(videos_to_process) * 7 / 60:.1f} hours)")
    
    proceed = input("\nProceed? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Cancelled.")
        return
    
    # Ask for model size
    print("\nWhisper model sizes:")
    print("  tiny   - Fastest, least accurate (~1 min per video)")
    print("  base   - Good balance (~5 min per video) [RECOMMENDED]")
    print("  small  - Better accuracy (~10 min per video)")
    print("  medium - Very good (~20 min per video)")
    
    model_size = input("Enter model size (default: base): ").strip() or "base"
    
    # Load Whisper model once
    print(f"\nLoading Whisper {model_size} model...")
    model = whisper.load_model(model_size)
    
    # Process each video
    successful = 0
    failed = 0
    skipped = 0
    
    for i, video in enumerate(videos_to_process, 1):
        print(f"\n[{i}/{len(videos_to_process)}] Processing: {video['title']}")
        print(f"  Video ID: {video['id']}")
        
        video_id = video['id']
        video_path = TEMP_DIR / f"{video_id}.mp4"
        audio_path = TEMP_DIR / f"{video_id}.mp3"
        vtt_path = TRANSCRIPT_DIR / f"{video_id}_en-x-autogen.vtt"
        
        try:
            # Download video
            if not video_path.exists():
                result = download_vimeo_video(video_id, video_path)
                if not result:
                    print(f"  FAILED: Could not download video")
                    failed += 1
                    continue
            else:
                print(f"  Using existing video file")
            
            # Extract audio
            if not audio_path.exists():
                result = extract_audio(video_path, audio_path)
                if not result:
                    print(f"  FAILED: Could not extract audio")
                    failed += 1
                    continue
            else:
                print(f"  Using existing audio file")
            
            # Transcribe
            result = transcribe_with_whisper(audio_path, model)
            
            # Create VTT
            create_vtt_file(result['segments'], vtt_path)
            print(f"  SUCCESS: VTT created")
            successful += 1
            
            # Cleanup
            cleanup_temp_files(video_id)
            
        except KeyboardInterrupt:
            print("\n\nStopped by user.")
            break
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 80)
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total processed: {successful + failed} / {len(videos_to_process)}")
    print(f"\nVTT files saved to: {TRANSCRIPT_DIR}")
    print("\nNext steps:")
    print("1. Run: python scripts/update_database.py")
    print("2. Run: push_database.bat")

if __name__ == "__main__":
    main()
