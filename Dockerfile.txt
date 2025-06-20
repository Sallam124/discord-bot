FROM python:3.11-slim

# Install unzip and any needed tools
RUN apt update && apt install -y unzip

# Set working directory
WORKDIR /app

# Copy all files into the container
COPY . .

# Unzip ffmpeg binary
RUN unzip ffmpeg.zip -d /usr/local/bin \
 && chmod +x /usr/local/bin/ffmpeg

# Make sure ffmpeg works
RUN ffmpeg -version

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run your bot
CMD ["python", "MusicBot.py"]
