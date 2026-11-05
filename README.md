# Stivos

Stivos is a class booking API for a fictional dance studio. Students book classes with a limited number of spots. When a class is full, the next person waits. When someone cancels, the first waiting student gets the spot.

The app and Postgres run in Docker. The tables are classes, students, and bookings. Startup loads fake classes and students. `GET /classes` lists each class and how many spots are left. `POST /bookings` books a student, and `POST /bookings/{booking_id}/cancel` cancels that booking.

## Run

Open Docker Desktop, then from this folder:

```bash
docker compose up --build
```

The first run downloads Postgres and installs the Python libraries. When the log says Uvicorn is running:

- Docs: http://localhost:8001/docs
- Health: http://localhost:8001/health
- Classes: http://localhost:8001/classes
- Book: `POST /bookings` with `student_id` and `class_id`
- Cancel: `POST /bookings/{booking_id}/cancel`

On this Mac, port 8000 and port 5432 are already taken. The app is on **8001**. Postgres is on **5433**. Inside Docker they still use 8000 and 5432.

Press Ctrl+C to stop the log. `docker compose down` stops the containers and keeps the data. `docker compose down -v` deletes the database too.

The page is a separate app. In another terminal, from this folder:

```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173. It talks to the API on port 8001. The API has to be running first.

With the stack already running, the booking tests are:

```bash
docker compose exec api pytest
```

A code change is copied into the image only when it is built, so run `docker compose up --build -d` before that command after you edit the app or the tests.

## What you should see

`GET /health` returns `{"status": "ok"}`.

`GET /classes` returns four classes. `spots_remaining` is the capacity minus bookings whose status is `booked`. The seed creates no bookings.

A new booking is `booked` while spots remain, and `waitlisted` when the class is full. Cancelling someone who held a spot promotes the oldest waiting booking for that class.

The local database user, password, and database name are all `stivos`. That password is only for this Docker database.

## Where the code lives

```text
app/main.py              starts the app, /health, creates tables
app/db.py                reads DATABASE_URL and opens Postgres
app/models.py            Class, Student, Booking
app/schemas.py           JSON shapes for classes and bookings
app/routers/classes.py   GET /classes
app/routers/bookings.py  booking routes
app/services/booking.py  booking rules
seed.py                  fake classes and students
Dockerfile               builds the API image
docker-compose.yml       starts the API and Postgres
web/                     React, TypeScript, and Vite page
```

`DATABASE_URL` in `docker-compose.yml` is the database address. The hostname `db` is the Compose service name.

`web/` is one page. It lists classes, books the student picked in the dropdown, and cancels a booking.

## What's next

- Later, Supabase for the database, Vercel for `web/`, and Railway for the API.
