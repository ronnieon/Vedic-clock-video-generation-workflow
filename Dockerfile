# Base image with Debian Bookworm (better tesseract support than slim/alpine)
FROM python:3.12-bookworm

# Prevent tzdata interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for tesseract, Pillow performance, and ffmpeg for moviepy
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-eng \
    libtesseract-dev libleptonica-dev \
    ffmpeg \
    libjpeg-dev zlib1g-dev libpng-dev libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy dependency list first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Health/diagnostic script (optional runtime check)
CMD ["python", "scripts/verify_ocr_env.py"]
