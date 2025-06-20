# Importing libraries and modules
import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
from collections import deque
import asyncio
import imageio_ffmpeg

# Load environment variables
load_dotenv()
TOKEN = 'MTM4NTcwMjUyNjE5NTU5NzM1Mg.GwjkVM.RTlFk0rHCG6UffPKep2KjCMFZnYcYiYXM-z-AA'

if TOKEN is None:
    print("ERROR: DISCORD_TOKEN not found in environment variables. Please check your .env file.")
    exit(1)

# Create the structure for queueing songs - Dictionary of queues
SONG_QUEUES = {}

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)


# Setup of intents. Intents are permissions the bot has on the server
intents = discord.Intents.default()
intents.message_content = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

# Bot ready-up code
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online!")
    bot.add_view(MusicControlPanel())


@bot.tree.command(name="skip", description="Skips the current playing song")
async def skip(interaction: discord.Interaction):
    try:
        voice_client = interaction.guild.voice_client
        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            voice_client.stop()
            await interaction.response.send_message("Skipped the current song.")
        else:
            await interaction.response.send_message("Not playing anything to skip.")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")


@bot.tree.command(name="pause", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction):
    try:
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            return await interaction.response.send_message("I'm not in a voice channel.")
        if not voice_client.is_playing():
            return await interaction.response.send_message("Nothing is currently playing.")
        voice_client.pause()
        await interaction.response.send_message("Playback paused!")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")


@bot.tree.command(name="resume", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction):
    try:
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            return await interaction.response.send_message("I'm not in a voice channel.")
        if not voice_client.is_paused():
            return await interaction.response.send_message("I'm not paused right now.")
        voice_client.resume()
        await interaction.response.send_message("Playback resumed!")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")


@bot.tree.command(name="stop", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    try:
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            return await interaction.response.send_message("I'm not connected to any voice channel.")
        guild_id_str = str(interaction.guild_id)
        if guild_id_str in SONG_QUEUES:
            SONG_QUEUES[guild_id_str].clear()
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        await voice_client.disconnect()
        await interaction.response.send_message("Stopped playback and disconnected!")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")


@bot.tree.command(name="play", description="Play a song or add it to the queue.")
@app_commands.describe(song_query="Search query")
async def play(interaction: discord.Interaction, song_query: str):
    try:
        await interaction.response.defer()
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("You must be in a voice channel to use this command.")
            return
        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            voice_client = await voice_channel.connect()
        elif voice_channel != voice_client.channel:
            await voice_client.move_to(voice_channel)
        ydl_options = {
            "format": "bestaudio[abr<=96]/bestaudio",
            "noplaylist": True,
            "youtube_include_dash_manifest": False,
            "youtube_include_hls_manifest": False,
        }
        query = "ytsearch1: " + song_query
        try:
            results = await asyncio.wait_for(search_ytdlp_async(query, ydl_options), timeout=10)
        except asyncio.TimeoutError:
            await interaction.followup.send("Song search timed out after 10 seconds. Please try a different query.")
            return
        tracks = results.get("entries", [])
        if not tracks:
            await interaction.followup.send("No results found.")
            return
        first_track = tracks[0]
        audio_url = first_track["url"]
        title = first_track.get("title", "Untitled")
        guild_id = str(interaction.guild_id)
        if SONG_QUEUES.get(guild_id) is None:
            SONG_QUEUES[guild_id] = deque()
        SONG_QUEUES[guild_id].append((audio_url, title))
        if voice_client.is_playing() or voice_client.is_paused():
            await interaction.followup.send(f"Added to queue: **{title}**")
        else:
            await interaction.followup.send(f"Now playing: **{title}**")
            await play_next_song(voice_client, guild_id, interaction.channel)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")


async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title = SONG_QUEUES[guild_id].popleft()
        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k",
        }
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"FFmpeg path: {ffmpeg_path}")
        print(f"Audio URL: {audio_url}")
        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable=ffmpeg_path)
        def after_play(error):
            if error:
                print(f"Error playing {title}: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)
        voice_client.play(source, after=after_play)
        asyncio.create_task(channel.send(f"Now playing: **{title}**"))
    else:
        await voice_client.disconnect()
        SONG_QUEUES[guild_id] = deque()


class MusicControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary, custom_id="pause_button")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("Playback paused!", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is currently playing.", ephemeral=True)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.success, custom_id="resume_button")
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("Playback resumed!", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is paused.", ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, custom_id="skip_button")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            voice_client.stop()
            await interaction.response.send_message("Skipped the current song.", ephemeral=True)
        else:
            await interaction.response.send_message("Not playing anything to skip.", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, custom_id="stop_button")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            guild_id_str = str(interaction.guild_id)
            if guild_id_str in SONG_QUEUES:
                SONG_QUEUES[guild_id_str].clear()
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
            await voice_client.disconnect()
            await interaction.response.send_message("Stopped playback and disconnected!", ephemeral=True)
        else:
            await interaction.response.send_message("I'm not connected to any voice channel.", ephemeral=True)


@bot.tree.command(name="panel", description="Show the music control panel with buttons.")
async def panel(interaction: discord.Interaction):
    await interaction.response.send_message("Music Control Panel:", view=MusicControlPanel(), ephemeral=False)


# Run the bot
bot.run(TOKEN)