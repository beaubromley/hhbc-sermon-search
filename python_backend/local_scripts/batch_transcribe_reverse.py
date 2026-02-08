# batch_transcribe_simple.py
import json
from pathlib import Path
import subprocess
import whisper
from datetime import timedelta
import threading
from queue import Queue
import time

TRANSCRIPT_DIR = Path('data/transcripts')
TEMP_DIR = Path('data/temp')
TEMP_DIR.mkdir(exist_ok=True)

# Your working Vimeo credentials
VIMEO_USERNAME = "beaubromley@gmail.com"
VIMEO_PASSWORD = "DC35npLj!!" 

# How many videos to download ahead
DOWNLOAD_BUFFER = 3

def format_timestamp(seconds):
    """Convert seconds to VTT timestamp format"""
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = int(td.total_seconds() % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def download_and_extract(video_id, video_path, audio_path):
    """Download audio only and convert - much faster!"""
    try:
        # Download ONLY audio stream directly as MP3
        cmd = [
            'yt-dlp',
            '--username', VIMEO_USERNAME,
            '--password', VIMEO_PASSWORD,
            '-f', 'bestaudio',  # Audio only!
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # Best quality
            '--postprocessor-args', '-ar 16000 -ac 1',  # 16kHz mono
            '-o', str(audio_path.with_suffix('')),  # Remove .mp3, yt-dlp adds it
            '--quiet',
            '--no-warnings',
            f'https://vimeo.com/{video_id}'
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
        # No FFmpeg extraction needed - yt-dlp does it all!
        return True
    except:
        return False

def download_worker(download_queue, stop_event):
    """Download worker - silent"""
    while not stop_event.is_set():
        try:
            try:
                video_info = download_queue.get(timeout=1)
            except:
                continue
            
            if video_info is None:
                break
            
            video_id, video_path, audio_path = video_info
            
            if not audio_path.exists():
                download_and_extract(video_id, video_path, audio_path)
            
            download_queue.task_done()
        except:
            pass

def create_vtt_file(segments, output_path):
    """Create VTT file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        for i, segment in enumerate(segments):
            start = format_timestamp(segment['start'])
            end = format_timestamp(segment['end'])
            text = segment['text'].strip()
            f.write(f"{i+1}\n{start} --> {end}\n{text}\n\n")
    return output_path

def cleanup_temp_files(video_id):
    """Cleanup temp files"""
    for f in TEMP_DIR.glob(f"{video_id}*"):
        try:
            f.unlink()
        except PermissionError:
            # File is locked by another process, skip it
            pass
        except Exception:
            # Any other error, skip it
            pass

def main():
    print("BATCH WHISPER TRANSCRIPTION")
    print("=" * 60)
    
    # Load videos
    with open(TRANSCRIPT_DIR / 'video_data.json', 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    # Find missing transcripts
    videos_to_process = [v for v in videos if not (TRANSCRIPT_DIR / f"{v['id']}_en-x-autogen.vtt").exists()]
    
    # REVERSE THE ORDER
    videos_to_process.reverse()
    
    print(f"Videos to process: {len(videos_to_process)}")
    
    if not videos_to_process:
        print("All done!")
        return
    
    if input("\nProceed? (y/n): ").lower() != 'y':
        return
    
    model_size = input("Model (tiny/base/small, default=base): ").strip() or "base"
    
    print(f"\nLoading Whisper {model_size} model...")
    model = whisper.load_model(model_size)
    
    # Start download workers
    download_queue = Queue(maxsize=DOWNLOAD_BUFFER)
    stop_event = threading.Event()
    
    workers = []
    for _ in range(2):
        t = threading.Thread(target=download_worker, args=(download_queue, stop_event))
        t.daemon = True
        t.start()
        workers.append(t)
    
    # Pre-load downloads
    for i in range(min(DOWNLOAD_BUFFER, len(videos_to_process))):
        v = videos_to_process[i]
        download_queue.put((v['id'], TEMP_DIR / f"{v['id']}.mp4", TEMP_DIR / f"{v['id']}.mp3"))
    
    print("\nProcessing...\n")
    
    successful = 0
    failed = 0
    
    try:
        for i, video in enumerate(videos_to_process):
            video_id = video['id']
            audio_path = TEMP_DIR / f"{video_id}.mp3"
            vtt_path = TRANSCRIPT_DIR / f"{video_id}_en-x-autogen.vtt"
            
            # Show what's queued for download
            print(f"\n[{i+1}/{len(videos_to_process)}] Current: {video['title'][:50]}")
            
            # Show download queue status
            queued_videos = []
            for j in range(1, min(DOWNLOAD_BUFFER + 1, len(videos_to_process) - i)):
                if i + j < len(videos_to_process):
                    queued_videos.append(videos_to_process[i + j]['id'])
            
            if queued_videos:
                print(f"  Downloading in background: {', '.join(queued_videos)}")
            
            # Wait for audio
            if not audio_path.exists():
                print(f"  Waiting for download...", end='', flush=True)
            
            wait = 0
            while not audio_path.exists() and wait < 600:
                time.sleep(1)
                wait += 1
                if wait % 10 == 0:
                    print(".", end='', flush=True)
            
            if audio_path.exists():
                print(" Ready!" if wait > 0 else "")
            
            if not audio_path.exists():
                print(f"  FAILED: Timeout")
                failed += 1
                
                # Queue next
                next_i = i + DOWNLOAD_BUFFER
                if next_i < len(videos_to_process):
                    nv = videos_to_process[next_i]
                    download_queue.put((nv['id'], TEMP_DIR / f"{nv['id']}.mp4", TEMP_DIR / f"{nv['id']}.mp3"))
                continue
            
            # Check if VTT already exists (other instance might have done it)
            if vtt_path.exists():
                print(f" ⏭️  Already done by other instance!")
                cleanup_temp_files(video_id)
                continue
            
            # Transcribe
            print(f"  Transcribing...", end='', flush=True)
            try:
                result = model.transcribe(str(audio_path), language='en', verbose=False)
                create_vtt_file(result['segments'], vtt_path)
                print(" ✅ Done!")
                successful += 1
            except Exception as e:
                print(f" ❌ Failed: {str(e)[:50]}")
                failed += 1
                # Delete corrupted file so it can be re-downloaded later
                if audio_path.exists():
                    audio_path.unlink()
            
            cleanup_temp_files(video_id)
            
            # Queue next
            next_i = i + DOWNLOAD_BUFFER
            if next_i < len(videos_to_process):
                nv = videos_to_process[next_i]
                download_queue.put((nv['id'], TEMP_DIR / f"{nv['id']}.mp4", TEMP_DIR / f"{nv['id']}.mp3"))
            
            # Progress summary
            if (i + 1) % 10 == 0:
                print(f"\n{'='*60}")
                print(f"Progress: {i+1}/{len(videos_to_process)} | Success: {successful} | Failed: {failed}")
                print(f"{'='*60}\n")
        
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        stop_event.set()
    
    stop_event.set()
    for _ in workers:
        download_queue.put(None)
    
    print("\n" + "=" * 60)
    print(f"COMPLETE: {successful} successful, {failed} failed")
    print("=" * 60)

if __name__ == "__main__":
    main()