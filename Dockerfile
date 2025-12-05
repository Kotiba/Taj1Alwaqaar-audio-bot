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

# Create a 1-second silent mp3 file (used as placeholder / keep-alive)
RUN mkdir -p audio_files && \
    ffmpeg -f lavfi -i anullsrc=channel_layout=mono:sample_rate=44100 \
           -t 1 -c:a libmp3lame -q:a 4 audio_files/silence.mp3

CMD ["python", "bot.py"]