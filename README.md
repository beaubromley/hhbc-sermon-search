# HHBC Sermon Search

**Live site: https://beaubromley.github.io/hhbc-sermon-search/**

Searchable archive of Henderson Hills Baptist Church sermons: stemmed full-text transcript search (ranked by best match, with typo suggestions and passage lookup like "Romans 8:28"), a sermon page with an embedded Vimeo player and a transcript that follows along, shareable links to any moment, speaker and series pages, related sermons, a video list, a Bible-reference heat map, saved sermons, and dark mode.

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

## Monitoring

The pipeline records a heartbeat in Turso (`sync_meta.last_sync`). `.github/workflows/freshness.yml` checks it daily and fails if it is more than 6 days old; GitHub emails the repo owner when a scheduled run fails. After changing the search index or vocabulary logic, run `python upload_to_turso.py --reindex` from `python_backend/` to rebuild them without re-uploading data.
