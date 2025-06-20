FROM python:3.11-slim

# Install ffmpeg and any basic system dependencies
RUN apt update && apt install -y ffmpeg

# Set working directory inside the container
WORKDIR /app

# Copy all files from your project into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set default command to run your bot
CMD ["python", "MusicBot.py"]
