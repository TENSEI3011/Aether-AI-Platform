# ============================================================
# Dockerfile — FastAPI Backend
# ============================================================
# Multi-stage build for the Python FastAPI backend.
# Usage: docker build -t ai-platform-backend ./backend
# ============================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing (pydub/ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create datasets directory
RUN mkdir -p /app/datasets /app/logs

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
