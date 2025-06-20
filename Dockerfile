FROM python:3.11-slim

# Install unzip and dependencies
RUN apt update && apt install -y unzip

# Set working directory
WORKDIR /app

# Copy all files into the container
COPY . .

# Unzip ffmpeg from nested path
RUN unzip bin/zip -d /usr/local/bin \
 && chmod +x /usr/local/bin/ffmpeg

# Make sure ffmpeg works
RUN ffmpeg -version

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run your bot
CMD ["python", "MusicBot.py"]
