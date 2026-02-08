import subprocess
import sys
from pathlib import Path
import time
import os

def run_script(script_path, description):
    """Run a Python script and handle errors"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {script_path}")
    
    try:
        # Run the script from the current directory
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=False, text=True, cwd=Path.cwd())
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
            return True
        else:
            print(f"❌ {description} failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {script_path}: {e}")
        return False

def run_interactive_script(script_path, description):
    """Run an interactive script without capturing output"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Starting: {script_path}")
    
    try:
        subprocess.run([
            sys.executable, script_path
        ], cwd=Path.cwd())
        return True
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
        print(f"📍 Make sure you're running this from the vimeo_project_v2 root directory")
        return False
    
    return True

def main():
    print("🎥 HHBC Sermon Search - Full Update Process")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not check_directory_structure():
        input("\nPress Enter to exit...")
        return
    
    print("\nThis will run the complete update process:")
    print("1. 📥 Download new videos and transcripts")
    print("2. 💾 Update the searchable database")
    print("3. 📖 Extract Bible references (new videos only)")
    print("4. 💭 Extract theological topics (new videos only)")
    print("5. 📊 Show updated statistics")
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
    
    # Step 3: Extract Bible references (incremental)
    run_script("local_scripts/extract_bible_references.py --incremental", "STEP 3: Extracting Bible References (New Videos)")
    
    time.sleep(2)
    
    # Step 4: Extract theological topics (incremental)
    run_script("local_scripts/extract_theological_topics.py --incremental", "STEP 4: Extracting Theological Topics (New Videos)")
    
    time.sleep(2)
    
    # Step 5: Show KPIs
    run_script("scripts/show_kpis.py", "STEP 5: Updated Statistics")
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n🎉 UPDATE PROCESS COMPLETED!")
    print(f"⏱️  Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    
    print(f"\n📌 NEXT STEPS:")
    print(f"1. Test locally: streamlit run streamlit_app.py")
    print(f"2. Push to GitHub: push_database.bat")
    print(f"3. Live site updates automatically in 1-2 minutes")
    
    print(f"\n👋 Update complete!")
    
if __name__ == "__main__":
    main()
