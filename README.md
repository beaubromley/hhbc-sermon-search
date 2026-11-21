# HHBC Sermon Search

**Live site: https://beaubromley.github.io/hhbc-sermon-search/**

Searchable archive of Henderson Hills Baptist Church sermons: full-text transcript search, a video list, and a Bible-reference heat map.

- `frontend/` - Vue 3 + Vite single-page app. Reads sermon data live from a Turso (libSQL) database over HTTP with a read-only token.
- `python_backend/` - the update pipeline: downloads new Vimeo videos and transcripts, updates the local SQLite database, extracts Bible references and topics, and syncs to Turso.

## Frontend

```
cd frontend
cp .env.example .env     # add the Turso URL + read-only token
npm install
npm run dev              # http://localhost:8082
npm run build
```

`VITE_BASE` sets the public path (`/` by default; the GitHub Pages workflow uses `/hhbc-sermon-search/`).
Pushing to `main` builds and deploys to GitHub Pages (`.github/workflows/deploy.yml`).

## Updating sermons

`python_backend/update_sermons.bat` runs the whole pipeline (`update_and_export.py`), then commits and pushes `speakers.json` if it changed. Windows Task Scheduler runs it (`HHBC Sermon Update`, Tuesday and Friday evenings); log output goes to `python_backend/logs/update.log`.
Needs `python_backend/src/config.py` (gitignored) with the Turso read/write token and Vimeo credentials.
