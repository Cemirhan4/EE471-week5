# ===================================================
# Dockerfile for EE471 Week-5 Task-1: Speech Studio
# Containerizes the Flask-based TTS & STT web app
# ===================================================
FROM python:3.11-slim

# Install system dependencies required by Azure Speech SDK and audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    ca-certificates \
    libasound2 \
    wget \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Create necessary directories for audio files
RUN mkdir -p static/audio static/uploads

# Expose the Flask port
EXPOSE 5000

# Set environment variables (defaults, override with docker run -e or .env)
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Run the Flask application
CMD ["python", "app.py"]
