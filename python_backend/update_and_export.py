import subprocess
import sys
from pathlib import Path
import time
import shutil

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

def split_database():
    """Split the compressed database into chunks for GitHub Pages"""
    print(f"\n{'='*60}")
    print("SPLITTING DATABASE FOR DEPLOYMENT")
    print(f"{'='*60}")
    
    frontend_data = Path('../frontend/public/data')
    input_file = frontend_data / 'transcripts.db.gz'
    
    if not input_file.exists():
        print(f"❌ {input_file} not found")
        return False
    
    chunk_size = 95 * 1024 * 1024  # 95 MB
    
    print(f"Splitting {input_file.name}...")
    print(f"Input size: {input_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    with open(input_file, 'rb') as f:
        chunk_num = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            output_file = frontend_data / f'transcripts.db.gz.part{chunk_num}'
            with open(output_file, 'wb') as out:
                out.write(chunk)
            
            print(f"  ✅ Created {output_file.name}: {len(chunk) / 1024 / 1024:.2f} MB")
            chunk_num += 1
    
    print(f"\n✅ Split into {chunk_num} chunks")
    return True

def main():
    print("🎥 HHBC Sermon Search - Full Update Process (Vue.js)")
    print("=" * 60)
    
    if not check_directory_structure():
        input("\nPress Enter to exit...")
        return
    
    print("\nThis will run the complete update process:")
    print("1. 📥 Download new videos and transcripts")
    print("2. 💾 Update the searchable database")
    print("3. 📖 Extract Bible references (new videos only)")
    print("4. 💭 Extract theological topics (new videos only)")
    print("5. 📤 Export to JSON for Vue.js frontend")
    print("6. ✂️  Split database into chunks for GitHub Pages")
    print("7. 📊 Show updated statistics")
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
    
    # Step 5: Export to JSON
    run_script("export_to_json.py", "STEP 5: Exporting Data to JSON")
    time.sleep(2)
    
    # Step 6: Split database
    split_database()
    time.sleep(2)
    
    # Step 7: Show KPIs
    run_script("scripts/show_kpis.py", "STEP 6: Updated Statistics")
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n🎉 UPDATE PROCESS COMPLETED!")
    print(f"⏱️  Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    
    print(f"\n📌 NEXT STEPS:")
    print(f"1. Test locally: cd ../frontend && npm run serve")
    print(f"2. Deploy to GitHub Pages:")
    print(f"   cd frontend")
    print(f"   npm run build")
    print(f"   cd dist")
    print(f"   [run git commands to push]")
    print(f"3. Live site updates automatically in 2-3 minutes")
    
    print(f"\n👋 Update complete!")

if __name__ == "__main__":
    main()
