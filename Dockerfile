# Use the same base image
FROM python:3.10-slim

# Set environment variables for cleaner logging and performance
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# FIX: Added '--no-install-recommends' to skip heavy GUI/X11 dependencies
# This reduces the download from ~700MB to ~50MB and prevents the timeout.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Generate the silence file (same logic as your logs, just cleaner format)
RUN mkdir -p audio_files && \
    ffmpeg -f lavfi -i anullsrc=r=44100:mono -t 1 -q:a 9 -acodec libmp3lame audio_files/silence.mp3

# Don't forget to set your start command (update 'main.py' to your actual script)
CMD ["python", "main.py"]