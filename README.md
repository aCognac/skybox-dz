# Skybox DZ

Self-hosted operations tool for skydiving dropzones. Polls live manifest data, detects SD cards from camera flyers, matches footage to jumpers per load, and syncs to cloud storage.

**Target:** Raspberry Pi 5, headless, SSD attached, USB SD card reader.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), SQLite |
| Frontend | React 18, Vite, nginx |
| Deployment | Docker Compose (ARM64-compatible) |
| SD detection | Python `watchdog` |
| Manifest polling | APScheduler background job |

---

## Quick Start

```bash
cp .env.example .env
# Edit .env — set VIDEO_STORAGE_PATH, SD_CARD_WATCH_PATH, BURBLE_BASE_URL

docker compose up --build
```

- Backend API + Swagger docs: `http://localhost:8000/docs`
- Frontend: `http://localhost`

---

## Scraper Tiers

| Tier | Description | Config |
|---|---|---|
| 1 | Cloud scraper (internet) | `BURBLE_BASE_URL=https://burble.com` |
| 2 | Local scraper (DZ wifi) | `BURBLE_BASE_URL=http://192.168.x.x` |
| 3 | Manual — no scraper | POST `/api/loads` with jumper names |

---

## Project Structure

```
skybox-dz/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan hooks
│   │   ├── config.py            # Settings via env vars
│   │   ├── database.py          # SQLAlchemy async setup
│   │   ├── models/              # VideoFile, Load, Assignment, SyncJob
│   │   ├── scrapers/            # base.py interface + burble.py adapter
│   │   ├── routers/             # /api/loads  /api/videos  /api/assignments
│   │   └── services/            # APScheduler (Burble poll) + watchdog (SD card)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/                     # React app
│   ├── nginx.conf               # Proxies /api → backend, SPA fallback
│   └── Dockerfile               # Multi-stage: node build → nginx serve
├── docker-compose.yml
└── .env.example
```

---

## Video Formats

| Format | Extension | Lenses |
|---|---|---|
| Insta360 | `.insv` | 2 (dual fisheye) |
| GoPro MAX | `.360` | 2 (dual fisheye) |
| Standard | `.mp4` | 1 |

Thumbnails are extracted per-lens via FFmpeg. File timestamps are used for sorting only — never for jumper matching.

---

## Development

```bash
# Backend only (hot reload)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend only (Vite dev server + API proxy to localhost:8000)
cd frontend
npm install
npm run dev
```
