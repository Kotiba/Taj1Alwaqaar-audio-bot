FROM python:3.10-slim

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Create audio_files directory and generate silence file
RUN mkdir -p audio_files && \
    ffmpeg -f lavfi -i anullsrc=r=44100:mono -t 1 -q:a 9 -acodec libmp3lame audio_files/silence.mp3

# Run the bot
CMD ["python", "bot.py"]