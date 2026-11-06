# Small Python image the API runs in.
FROM python:3.12-slim

# Working folder inside the container.
WORKDIR /app

# Install libraries before copying the rest, so a code change does not reinstall them.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The app listens on 8000 inside the container. The Mac reaches it on 8001.
EXPOSE 8000

# Seed first, then start the server. Seed skips rows that already exist.
CMD ["sh", "-c", "python seed.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
