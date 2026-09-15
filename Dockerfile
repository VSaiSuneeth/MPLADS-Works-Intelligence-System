FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Pillow, audio processing, and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend /app

# Create upload directories
RUN mkdir -p /data/uploads/photos /data/uploads/voice /data/uploads/notes

ENV PYTHONPATH=/app
ENV UPLOAD_DIR=/data/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
