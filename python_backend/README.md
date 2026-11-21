# Python backend (update pipeline)

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
update_sermons.bat        # full pipeline: download -> database -> references/topics -> speakers.json -> Turso
```

Steps are listed in `update_and_export.py`. `src/config.py` (gitignored) holds credentials.
