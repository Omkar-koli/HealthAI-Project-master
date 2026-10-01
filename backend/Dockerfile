# Save this file as: backend/Dockerfile  (rename when you place it)

FROM python:3.10-slim

WORKDIR /app

# System libraries needed by Pillow / TensorFlow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching: this step
# only re-runs if requirements.txt changes, not on every code edit)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Now copy the actual application code and model
# (backend/ as a package, models/ alongside it, matching BASE_DIR in config.py)
COPY backend/ ./backend/
COPY models/ ./models/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
