# create_v3_structure.py
import os
from pathlib import Path
import shutil

def create_v3_structure():
    """Create the v3 project structure in existing folder"""
    
    print("Creating v3 project structure...")
    print("=" * 60)
    
    v3_dir = Path("C:/Users/beaub/OneDrive/Python/Vimeo Downloader/vimeo_project_v3")
    
    # Check if v3 exists
    if not v3_dir.exists():
        print(f"ERROR: {v3_dir} not found!")
        print("Please copy vimeo_project_v2 to vimeo_project_v3 first")
        return
    
    # Create new directories for JavaScript frontend
    print(f"\n1. Creating frontend structure...")
    
    frontend_dir = v3_dir / "frontend"
    frontend_dir.mkdir(exist_ok=True)
    
    # Frontend subdirectories
    (frontend_dir / "public").mkdir(exist_ok=True)
    (frontend_dir / "public" / "data").mkdir(exist_ok=True)
    (frontend_dir / "public" / "assets").mkdir(exist_ok=True)
    (frontend_dir / "src").mkdir(exist_ok=True)
    (frontend_dir / "src" / "components").mkdir(exist_ok=True)
    (frontend_dir / "src" / "views").mkdir(exist_ok=True)
    
    print("   ✅ Created frontend directories!")
    
    # Rename existing folders
    print(f"\n2. Organizing Python backend...")
    python_backend = v3_dir / "python_backend"
    
    # Move Python stuff to python_backend folder
    python_backend.mkdir(exist_ok=True)
    
    folders_to_move = ['src', 'scripts', 'local_scripts', 'data']
    files_to_move = ['update_and_run.py', 'push_database.bat', 'requirements_local.txt', 'how to use.txt', 'streamlit_app.py', 'requirements.txt']
    
    for folder in folders_to_move:
        src = v3_dir / folder
        dst = python_backend / folder
        if src.exists() and src != dst:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.move(str(src), str(dst))
            print(f"   Moved {folder}/")
    
    for file in files_to_move:
        src = v3_dir / file
        dst = python_backend / file
        if src.exists() and src != dst:
            if dst.exists():
                dst.unlink()
            shutil.move(str(src), str(dst))
            print(f"   Moved {file}")
    
    print("   ✅ Organized Python backend!")
    
    # Create placeholder files
    print(f"\n3. Creating placeholder files...")
    
    # README
    with open(v3_dir / "README.md", 'w') as f:
        f.write("""# HHBC Sermon Search - JavaScript Version

## Structure

- `python_backend/` - Python scripts for data processing
- `frontend/` - Vue.js web application
- `docs/` - GitHub Pages deployment (generated)

## Setup

See individual folders for setup instructions.
""")
    
    # Frontend README
    with open(frontend_dir / "README.md", 'w') as f:
        f.write("""# HHBC Sermon Search - Frontend

Vue.js application for searching sermons.

## Setup

1. Install Node.js
2. Run: `npm install`
3. Run: `npm run serve`

## Build for Production

`npm run build`

Outputs to `../docs/` for GitHub Pages deployment.
""")
    
    # Python backend README
    with open(python_backend / "README.md", 'w') as f:
        f.write("""# HHBC Sermon Search - Python Backend

Data processing and export scripts.

## Setup

1. Create venv: `python -m venv venv`
2. Activate: `venv\\Scripts\\activate`
3. Install: `pip install -r requirements_local.txt`

## Export Data for Frontend

Run: `python export_to_json.py`

This exports the SQLite database to JSON files in `../frontend/public/data/`
""")
    
    print("   ✅ Created README files!")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ V3 PROJECT STRUCTURE CREATED!")
    print("=" * 60)
    print(f"\nLocation: {v3_dir}")
    print("\nStructure:")
    print("  vimeo_project_v3/")
    print("  ├── python_backend/      (All your Python code)")
    print("  ├── frontend/            (Vue.js app - empty, ready to build)")
    print("  ├── docs/                (Will be created by Vue build)")
    print("  └── README.md")
    print("\nNext steps:")
    print("1. Install Node.js: winget install OpenJS.NodeJS")
    print("2. Close and reopen terminal")
    print("3. Install Vue CLI: npm install -g @vue/cli")
    print("4. Create Vue app: cd frontend && vue create .")
    print("\nReady to build the JavaScript version!")

if __name__ == "__main__":
    create_v3_structure()
