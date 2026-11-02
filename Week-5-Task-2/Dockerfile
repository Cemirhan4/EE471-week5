# ============================================================
# Dockerfile for EE471 Week-5 Task-2: Voice-Activated Calculator
# Containerizes the Flask-based voice calculator web app
# ============================================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Expose the Flask port
EXPOSE 5002

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Run the Flask application
CMD ["python", "app.py"]
