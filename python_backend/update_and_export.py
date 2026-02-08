import subprocess
import sys
from pathlib import Path
import time
import sqlite3

def run_script(script_path, description, args=None):
    """Run a Python script and handle errors"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {script_path}")

    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd, capture_output=False, text=True, cwd=Path.cwd()
        )

        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
            return True
        else:
            print(f"❌ {description} failed with return code: {result.returncode}")
            return False

    except Exception as e:
        print(f"❌ Error running {script_path}: {e}")
        return False

def check_directory_structure():
    """Verify we're in the right directory"""
    current_dir = Path.cwd()
    required_folders = ['data', 'scripts', 'src']

    print(f"📁 Current directory: {current_dir}")
    print(f"📂 Checking for required folders...")

    missing_folders = []
    for folder in required_folders:
        folder_path = current_dir / folder
        if folder_path.exists():
            print(f"  ✅ {folder}/ found")
        else:
            print(f"  ❌ {folder}/ NOT found")
            missing_folders.append(folder)

    if missing_folders:
        print(f"\n❌ ERROR: Missing required folders: {missing_folders}")
        print(f"📍 Make sure you're running this from the python_backend directory")
        return False

    return True

def rebuild_fts5():
    """Rebuild the FTS5 full-text search index on the local database"""
    print(f"\n{'='*60}")
    print("REBUILDING FTS5 SEARCH INDEX")
    print(f"{'='*60}")

    db_path = Path('data/database/transcripts.db')
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return False

    conn = sqlite3.connect(str(db_path))
    try:
        # Drop and recreate the FTS5 external content table
        conn.execute('DROP TABLE IF EXISTS transcript_fts')
        conn.execute('''CREATE VIRTUAL TABLE transcript_fts USING fts5(
            text,
            content=transcript_segments,
            content_rowid=rowid
        )''')
        conn.execute("INSERT INTO transcript_fts(transcript_fts) VALUES('rebuild')")
        conn.commit()

        # Report size
        row_count = conn.execute('SELECT COUNT(*) FROM transcript_fts').fetchone()[0]
        print(f"  ✅ FTS5 index rebuilt with {row_count:,} segments")
        return True
    except Exception as e:
        print(f"  ❌ Error rebuilding FTS5: {e}")
        return False
    finally:
        conn.close()

def main():
    print("🎥 HHBC Sermon Search - Full Update Process")
    print("=" * 60)

    if not check_directory_structure():
        input("\nPress Enter to exit...")
        return

    print("\nThis will run the complete update process:")
    print("1. 📥 Download new videos and transcripts")
    print("2. 💾 Update the searchable database")
    print("3. 📖 Extract Bible references (new videos only)")
    print("4. 💭 Extract theological topics (new videos only)")
    print("5. 📤 Export speakers.json for frontend")
    print("6. 🔍 Rebuild FTS5 search index")
    print("7. ☁️  Sync database to Turso")
    print("8. 📊 Show updated statistics")
    print()

    start_time = time.time()

    # Step 1: Download videos
    if not run_script("scripts/download_videos_incremental.py", "STEP 1: Downloading Videos & Transcripts"):
        print("\n⚠️  Download had issues, but continuing...")
    time.sleep(2)

    # Step 2: Update database
    if not run_script("scripts/update_database.py", "STEP 2: Updating Transcript Database"):
        print("\n⚠️  Database update had issues, but continuing...")
    time.sleep(2)

    # Step 3: Extract Bible references (incremental - new videos only)
    run_script("local_scripts/extract_bible_references.py", "STEP 3: Extracting Bible References (New Videos)", args=["--incremental"])
    time.sleep(2)

    # Step 4: Extract theological topics (incremental - new videos only)
    run_script("local_scripts/extract_theological_topics.py", "STEP 4: Extracting Theological Topics (New Videos)", args=["--incremental"])
    time.sleep(2)

    # Step 5: Export speakers.json (only JSON file still needed by frontend)
    run_script("export_to_json.py", "STEP 5: Exporting Speakers JSON")
    time.sleep(2)

    # Step 6: Rebuild FTS5 search index on local database
    rebuild_fts5()
    time.sleep(2)

    # Step 7: Sync to Turso (full re-upload + FTS5 rebuild on remote)
    run_script("upload_to_turso.py", "STEP 7: Syncing Database to Turso")
    time.sleep(2)

    # Step 8: Show KPIs
    run_script("scripts/show_kpis.py", "STEP 8: Updated Statistics")

    # Summary
    end_time = time.time()
    duration = end_time - start_time

    print(f"\n🎉 UPDATE PROCESS COMPLETED!")
    print(f"⏱️  Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")

    print(f"\n📌 NEXT STEPS:")
    print(f"1. Test locally: cd ../frontend && npm run serve")
    print(f"2. Push to GitHub: git add -A && git commit && git push")
    print(f"3. GitHub Actions will auto-deploy to GitHub Pages")

    print(f"\n👋 Update complete!")

if __name__ == "__main__":
    main()
