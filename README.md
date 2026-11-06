# Stivos

Stivos is a class booking app for a fictional dance studio. Students book classes with a limited number of spots. When a class is full, the next person waits. When someone cancels, the first waiting student gets the spot.

## Live

- Page: https://stivos.vercel.app/

| Piece | Host |
|-------|------|
| Page (`web/`) | Vercel |
| API (`app/`) | Railway |
| Database | Supabase (Postgres) |

The page calls the Railway API. The API reads and writes Supabase. `seed.py` only fills missing classes and students; it does not replace the database.

## Local run

1. Copy your Supabase connection string into a local `.env` file (never commit this file):

```bash
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres
```

Use the Session-mode URI from Supabase, with `+psycopg` after `postgresql`.

2. Open Docker Desktop, then from this folder:

```bash
docker compose up --build
```

Compose passes `DATABASE_URL` into the API container. On this Mac the API is on **8001**. A local Postgres container may still start, but the API uses Supabase when `.env` is set.

When the log says Uvicorn is running:

- Docs: http://localhost:8001/docs
- Health: http://localhost:8001/health
- Classes: http://localhost:8001/classes

3. In another terminal, start the page:

```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173 (or 5174 if 5173 is taken). It talks to the API on port 8001.

### Tests

With the stack already running:

```bash
docker compose exec api pytest
```

Rebuild after API or test edits: `docker compose up --build -d`.

## Cloud env vars

**Railway (API)**

- `DATABASE_URL` — same Supabase URL as local `.env`
- `CORS_ORIGINS` — optional extra origins (comma-separated). `*.vercel.app` is already allowed in code.
- `PORT` — set by Railway; the Dockerfile uses `${PORT:-8000}`

**Vercel (page, root directory `web`)**

- `VITE_API_URL` — Railway public URL with no trailing slash, for example `https://stivos-production.up.railway.app`  
  Use Production (and Redeploy after changing it). This value is public in the browser; that is expected.

Do not put passwords or `.env` contents in git or in this README.

## What you should see

`GET /health` returns `{"status": "ok"}`.

`GET /classes` returns the seeded classes. `spots_remaining` is capacity minus bookings whose status is `booked`.

A new booking is `booked` while spots remain, and `waitlisted` when the class is full. Cancelling a booked spot promotes the oldest waitlisted booking for that class. Booking locks the class row so two requests cannot take the last spot.

## Where the code lives

```text
app/main.py              starts the app, CORS, /health
app/db.py                reads DATABASE_URL and opens Postgres
app/models.py            Class, Student, Booking
app/schemas.py           JSON shapes for classes, students, bookings
app/routers/classes.py   GET /classes
app/routers/students.py  GET /students
app/routers/bookings.py  booking routes
app/services/booking.py  booking rules and row lock
seed.py                  fake classes and students when missing
tests/                   booking pytest suite
Dockerfile               API image for Docker and Railway
docker-compose.yml       local API (and optional local Postgres)
web/                     React, TypeScript, and Vite page
```
