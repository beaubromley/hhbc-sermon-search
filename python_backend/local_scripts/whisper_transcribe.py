# whisper_transcribe.py
import whisper
import subprocess
import json
import subprocess
from pathlib import Path
from datetime import timedelta
import requests


TRANSCRIPT_DIR = Path('data/transcripts')
TEMP_DIR = Path('data/temp')
TEMP_DIR.mkdir(exist_ok=True)

def format_timestamp(seconds):
    """Convert seconds to VTT timestamp format (HH:MM:SS.mmm)"""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def download_vimeo_video(video_id, output_path):
    """Download video from Vimeo using yt-dlp with authentication"""
    print(f"Downloading video {video_id} using yt-dlp...")
    
    # Hardcode your Vimeo credentials here (don't push this file to GitHub!)
    vimeo_username = "beaubromley@gmail.com"
    vimeo_password = "DC35npLj!!" 
    
    temp_dir = output_path.parent
    
    cmd = [
        'yt-dlp',
        '--username', vimeo_username,
        '--password', vimeo_password,
        '-o', str(output_path),
        f'https://vimeo.com/{video_id}'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        # Check if merged file exists
        if output_path.exists():
            print(f"Video downloaded to: {output_path}")
            return output_path
        
        # If not, look for separate video and audio files and merge them
        video_files = list(temp_dir.glob(f"{video_id}*.mp4"))
        if len(video_files) >= 2:
            print(f"Found {len(video_files)} separate files. Merging with FFmpeg...")
            
            # Find video and audio files
            video_file = None
            audio_file = None
            for f in video_files:
                if 'audio' in f.name.lower():
                    audio_file = f
                else:
                    video_file = f
            
            if video_file and audio_file:
                # Merge with FFmpeg
                merge_cmd = [
                    'ffmpeg',
                    '-i', str(video_file),
                    '-i', str(audio_file),
                    '-c', 'copy',  # Copy streams without re-encoding
                    '-y',  # Overwrite
                    str(output_path)
                ]
                
                subprocess.run(merge_cmd, check=True, capture_output=True)
                print(f"Merged video saved to: {output_path}")
                
                # Clean up separate files
                video_file.unlink()
                audio_file.unlink()
                print("Cleaned up temporary files")
                
                return output_path
        
        print(f"ERROR: Could not find or merge video files")
        return None
            
    except subprocess.CalledProcessError as e:
        print(f"Download/merge failed!")
        print(f"Error: {e}")
        return None



def extract_audio(video_path, audio_path):
    """Extract audio from video using FFmpeg"""
    print(f"Extracting audio from {video_path.name}...")
    
    cmd = [
        'ffmpeg',
        '-i', str(video_path),
        '-vn',  # No video
        '-acodec', 'libmp3lame',  # MP3 codec
        '-ar', '16000',  # 16kHz sample rate (Whisper works well with this)
        '-ac', '1',  # Mono
        '-y',  # Overwrite output file
        str(audio_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Audio extracted to: {audio_path}")
        return audio_path
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        return None
    except FileNotFoundError:
        print("ERROR: FFmpeg not found!")
        print("Install FFmpeg from: https://ffmpeg.org/download.html")
        print("Or use: winget install ffmpeg (on Windows)")
        return None

def transcribe_with_whisper(audio_path, model_size="base"):
    """Transcribe audio using Whisper"""
    print(f"Loading Whisper model ({model_size})...")
    print("This may take a few minutes on first run (downloading model)...")
    
    model = whisper.load_model(model_size)
    
    print(f"Transcribing {audio_path.name}...")
    print("This will take a while depending on audio length...")
    
    result = model.transcribe(
        str(audio_path),
        language='en',
        verbose=True  # Show progress
    )
    
    return result

def create_vtt_file(segments, output_path):
    """Create VTT file from Whisper segments"""
    print(f"Creating VTT file: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        
        for i, segment in enumerate(segments):
            start = format_timestamp(segment['start'])
            end = format_timestamp(segment['end'])
            text = segment['text'].strip()
            
            f.write(f"{i+1}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
    
    print(f"VTT file created successfully!")
    return output_path

def process_video(video_id, model_size="base"):
    """Complete workflow: download → extract → transcribe → create VTT"""
    print("=" * 80)
    print(f"PROCESSING VIDEO: {video_id}")
    print("=" * 80)
    
    # File paths
    video_path = TEMP_DIR / f"{video_id}.mp4"
    audio_path = TEMP_DIR / f"{video_id}.mp3"
    vtt_path = TRANSCRIPT_DIR / f"{video_id}_en-x-autogen.vtt"
    
    # Step 1: Download video (manual for now)
    if not video_path.exists():
        download_vimeo_video(video_id, video_path)
    
    if not video_path.exists():
        print("ERROR: Video file not found. Cannot continue.")
        return None
    
    # Step 2: Extract audio
    if not audio_path.exists():
        audio_path = extract_audio(video_path, audio_path)
        if not audio_path:
            return None
    else:
        print(f"Using existing audio file: {audio_path}")
    
    # Step 3: Transcribe with Whisper
    print("\nStarting transcription...")
    result = transcribe_with_whisper(audio_path, model_size)
    
    # Step 4: Create VTT file
    vtt_path = create_vtt_file(result['segments'], vtt_path)
    
    # Cleanup temp files (optional)
    cleanup = input("\nDelete temporary video/audio files? (y/n): ").lower()
    if cleanup == 'y':
        if video_path.exists():
            video_path.unlink()
            print(f"Deleted: {video_path}")
        if audio_path.exists():
            audio_path.unlink()
            print(f"Deleted: {audio_path}")
    
    print("\n" + "=" * 80)
    print("COMPLETE!")
    print(f"VTT file saved to: {vtt_path}")
    print("=" * 80)
    
    return vtt_path

if __name__ == "__main__":
    print("Whisper Transcription Tool")
    print("=" * 80)
    print("\nModel sizes:")
    print("  tiny   - Fastest, least accurate")
    print("  base   - Good balance (RECOMMENDED)")
    print("  small  - Better accuracy, slower")
    print("  medium - Very good, quite slow")
    print("  large  - Best accuracy, very slow")
    
    video_id = input("\nEnter Vimeo video ID: ").strip()
    model_size = input("Enter model size (default: base): ").strip() or "base"
    
    process_video(video_id, model_size)
