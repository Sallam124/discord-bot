# Discord Music Bot

A simple, modern Discord music bot built with Python, using slash commands.

## Features

-   Plays music from YouTube (links or search).
-   Song queuing system.
-   Modern slash commands (`/play`, `/skip`, `/queue`, `/leave`).
-   Automatically manages FFmpeg dependency.
-   Ready for deployment on platforms like Railway using Docker.

## Setup

### 1. Create a Discord Bot Application

-   Go to the [Discord Developer Portal](https://discord.com/developers/applications).
-   Create a new application.
-   Go to the "Bot" tab and click "Add Bot".
-   Under "Privileged Gateway Intents", enable **"Message Content Intent"**.
-   Copy the bot's **token**.

### 2. Environment Variables

-   Create a file named `.env` in the root of your project.
-   Add your bot token to this file:
    ```
    DISCORD_TOKEN=your_bot_token_here
    ```

### 3. Running Locally

-   Install Python 3.9 or higher.
-   Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```
-   Run the bot:
    ```sh
    python MusicBot.py
    ```

### 4. Deploying to Railway (or similar platforms)

-   Push your code to a GitHub repository.
-   Create a new project on Railway and connect it to your GitHub repo.
-   Railway will automatically use the `Dockerfile` to build and deploy your bot.
-   Go to your service's "Variables" tab on Railway and add your `DISCORD_TOKEN`.

## Commands

-   `/play <query>`: Plays a song from a YouTube URL or search query.
-   `/skip`: Skips the currently playing song.
-   `/queue`: Shows the current song queue.
-   `/leave`: Disconnects the bot from the voice channel and clears the queue. 