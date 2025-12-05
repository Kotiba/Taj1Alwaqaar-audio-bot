# 1. We start with a dedicated image that contains a static FFmpeg binary
FROM mwader/static-ffmpeg:7.0 AS ffmpeg-source

# 2. We start your actual Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# --- THE FIX ---
# Instead of 'apt-get install ffmpeg', we copy the binary from the first stage.
# This skips installing 200+ dependencies (X11, Wayland, Mesa, etc).
COPY --from=ffmpeg-source /ffmpeg /usr/local/bin/
COPY --from=ffmpeg-source /ffprobe /usr/local/bin/
# ----------------

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Create the silence file (using the static ffmpeg we just copied)
RUN mkdir -p audio_files && \
    ffmpeg -f lavfi -i anullsrc=r=44100:mono -t 1 -q:a 9 -acodec libmp3lame audio_files/silence.mp3

CMD ["python", "main.py"]