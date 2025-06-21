import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import yt_dlp
from collections import deque
import asyncio
import random
import urllib.parse

# Load environment variables
load_dotenv()
DISCORD_TOKEN = 'MTM4NTcwMjUyNjE5NTU5NzM1Mg.GBq_KE.yX2U9zwaLTsTrcnPrkZ_EsOt8lAI-zO_5IxE3g'
FFMPEG_PATH = "ffmpeg"  # Let the system path resolve it

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# In-memory queue for songs
SONG_QUEUES = {}
NOW_PLAYING = {}
DISCONNECT_TASKS = {}

# --- Path to your local FFmpeg executable ---
# For Windows, use double backslashes or forward slashes
FFMPEG_PATH = "bin/ffmpeg/ffmpeg.exe"

def get_queue(guild_id):
    if guild_id not in SONG_QUEUES:
        SONG_QUEUES[guild_id] = deque()
    return SONG_QUEUES[guild_id]

async def disconnect_after_inactivity(voice_client, guild_id, channel):
    """Waits 15 minutes, then disconnects if the bot is inactive."""
    await asyncio.sleep(900) # 15 minutes
    
    if voice_client.is_connected() and not voice_client.is_playing() and not voice_client.is_paused() and not get_queue(guild_id):
        await voice_client.disconnect()
        if guild_id in SONG_QUEUES:
            del SONG_QUEUES[guild_id]
        if guild_id in NOW_PLAYING:
            del NOW_PLAYING[guild_id]
        if guild_id in DISCONNECT_TASKS:
            del DISCONNECT_TASKS[guild_id]
        await channel.send("Left the voice channel due to 15 minutes of inactivity.")

async def play_next_song(voice_client, guild_id, channel):
    queue = get_queue(guild_id)
    if queue:
        audio_url, title = queue.popleft()
        NOW_PLAYING[guild_id] = title
        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }
        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable=FFMPEG_PATH)
        
        def after_play(error):
            if error:
                print(f"Error playing {title}: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)
            
        voice_client.play(source, after=after_play)
        await channel.send(f"Now playing: **{title}**")
    else:
        if guild_id in NOW_PLAYING:
            del NOW_PLAYING[guild_id]
        
        task = bot.loop.create_task(disconnect_after_inactivity(voice_client, guild_id, channel))
        DISCONNECT_TASKS[guild_id] = task

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    try:
        # Force sync all commands
        await bot.wait_until_ready()
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command(name="sa3edni", description="Shows a list of all available commands.")
async def sa3edni_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎧 Music Bot Commands 🎧",
        description="Here are all the available commands:",
        color=discord.Color.blue()
    )
    
    # Define all available commands manually to ensure they're all included
    commands_info = [
        ("sa3edni", "Shows a list of all available commands."),
        ("play", "Play a song from YouTube (link or search)"),
        ("skip", "Skip the current song"),
        ("previous", "Go back to the previous song (shows current song info)"),
        ("pause", "Pauses the current song"),
        ("resume", "Resumes the current song"),
        ("nowplaying", "Shows the currently playing song"),
        ("shuffle", "Shuffles the song queue"),
        ("random", "Plays a random selection of popular songs."),
        ("queue", "Display the current song queue"),
        ("etla3", "Disconnect the bot from the voice channel")
    ]
    
    # Sort commands alphabetically
    commands_info.sort(key=lambda x: x[0])
    
    for command_name, description in commands_info:
        embed.add_field(name=f"/{command_name}", value=description, inline=False)
        
    embed.set_footer(text="Use the commands with a forward slash, e.g., /play")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="play", description="Play a song from YouTube (link or search)")
@app_commands.describe(query="A YouTube URL or search query")
async def play(interaction: discord.Interaction, query: str):
    voice_channel = interaction.user.voice.channel
    if not voice_channel:
        await interaction.response.send_message("You need to be in a voice channel!", ephemeral=True)
        return

    await interaction.response.defer()

    guild_id = interaction.guild_id
    if guild_id in DISCONNECT_TASKS:
        DISCONNECT_TASKS[guild_id].cancel()
        del DISCONNECT_TASKS[guild_id]

    # Clean up the query URL if it's a playlist
    query_url = query
    is_playlist = False
    try:
        parsed_url = urllib.parse.urlparse(query)
        if 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
            params = urllib.parse.parse_qs(parsed_url.query)
            if 'list' in params:
                playlist_id = params['list'][0]
                # YouTube Mix playlists (starting with RD) are unviewable. 
                # In this case, we'll just play the video from the 'v' param.
                if playlist_id.startswith('RD') and 'v' in params:
                    video_id = params['v'][0]
                    query_url = f'https://www.youtube.com/watch?v={video_id}'
                    is_playlist = False
                else:
                    query_url = f'https://www.youtube.com/playlist?list={playlist_id}'
                    is_playlist = True
    except Exception:
        pass # Not a valid URL, treat as search query

    ydl_options = {
        "format": "bestaudio/best",
        "quiet": True,
        "default_search": "ytsearch",
        "extract_flat": "in_playlist" if is_playlist else False,
    }
    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        try:
            info = ydl.extract_info(query_url, download=False)
            
            queue = get_queue(interaction.guild_id)
            
            if 'entries' in info:
                # It's a playlist
                playlist_title = info.get('title', 'a playlist')
                await interaction.followup.send(f"Queuing playlist: **{playlist_title}**")
                
                for entry in info['entries']:
                    try:
                        # We need to re-extract with download=True to get a streamable URL
                        entry_info = ydl.extract_info(entry['url'], download=False)
                        audio_url = entry_info["url"]
                        title = entry_info["title"]
                        queue.append((audio_url, title))
                    except Exception as e:
                        print(f"Couldn't queue {entry.get('title', 'a video')}: {e}")
                        pass # Continue with other songs

                # Auto-shuffle playlists for better variety
                if len(queue) > 1:
                    queue_list = list(queue)
                    random.shuffle(queue_list)
                    SONG_QUEUES[interaction.guild_id] = deque(queue_list)
                    await interaction.followup.send(f"Playlist queued and shuffled! ({len(queue)} songs)")

            else:
                # It's a single video
                audio_url = info["url"]
                title = info["title"]
                queue.append((audio_url, title))
                await interaction.followup.send(f"Queued: **{title}**")

            voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
            if not voice_client or not voice_client.is_connected():
                voice_client = await voice_channel.connect()
            
            if not voice_client.is_playing() and not voice_client.is_paused():
                await play_next_song(voice_client, interaction.guild_id, interaction.channel)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

@bot.tree.command(name="skip", description="Skip the current song")
async def skip(interaction: discord.Interaction):
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("Skipped the song.")
    else:
        await interaction.response.send_message("Nothing is playing to skip.", ephemeral=True)

@bot.tree.command(name="previous", description="Go back to the previous song")
async def previous_command(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    
    # Check if there's a previous song to go back to
    if guild_id in NOW_PLAYING:
        current_song = NOW_PLAYING[guild_id]
        queue = get_queue(guild_id)
        
        # For now, we'll just show what the current song is
        # In a full implementation, you'd need to track song history
        await interaction.response.send_message(f"Current song: **{current_song}**. Previous song functionality requires song history tracking.", ephemeral=True)
    else:
        await interaction.response.send_message("Nothing is currently playing.", ephemeral=True)

@bot.tree.command(name="pause", description="Pauses the current song")
async def pause(interaction: discord.Interaction):
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("Paused the song.")
    else:
        await interaction.response.send_message("Nothing is playing to pause.", ephemeral=True)

@bot.tree.command(name="resume", description="Resumes the current song")
async def resume(interaction: discord.Interaction):
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("Resumed the song.")
    else:
        await interaction.response.send_message("The bot is not paused.", ephemeral=True)

@bot.tree.command(name="nowplaying", description="Shows the currently playing song")
async def nowplaying(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    if guild_id in NOW_PLAYING:
        await interaction.response.send_message(f"Now playing: **{NOW_PLAYING[guild_id]}**")
    else:
        await interaction.response.send_message("Nothing is currently playing.", ephemeral=True)

@bot.tree.command(name="shuffle", description="Shuffles the song queue")
async def shuffle(interaction: discord.Interaction):
    queue = get_queue(interaction.guild_id)
    if len(queue) > 1:
        queue_list = list(queue)
        random.shuffle(queue_list)
        SONG_QUEUES[interaction.guild_id] = deque(queue_list)
        await interaction.response.send_message("Queue has been shuffled.")
    else:
        await interaction.response.send_message("Not enough songs in the queue to shuffle.", ephemeral=True)

@bot.tree.command(name="random", description="Plays a random selection of popular songs.")
async def random_command(interaction: discord.Interaction):
    voice_channel = interaction.user.voice.channel
    if not voice_channel:
        await interaction.response.send_message("You need to be in a voice channel!", ephemeral=True)
        return

    await interaction.response.defer()

    guild_id = interaction.guild_id
    if guild_id in DISCONNECT_TASKS:
        DISCONNECT_TASKS[guild_id].cancel()
        del DISCONNECT_TASKS[guild_id]

    # Search for a popular playlist
    query = "Top 100 Global Songs"
    
    ydl_search_options = {
        "format": "bestaudio/best",
        "quiet": True,
        "default_search": "ytsearch1", # Search for one playlist
        "extract_flat": "playlist", # Get playlist info without extracting each video
    }

    ydl_extract_options = {
        "format": "bestaudio/best",
        "quiet": True,
    }
    
    with yt_dlp.YoutubeDL(ydl_search_options) as ydl:
        try:
            # Search for the playlist
            search_result = ydl.extract_info(query, download=False)
            
            if not search_result or 'entries' not in search_result or not search_result['entries']:
                 await interaction.followup.send("Could not find a suitable playlist to play random songs.", ephemeral=True)
                 return

            playlist_title = search_result.get('title', 'a random playlist')
            await interaction.followup.send(f"Found playlist: **{playlist_title}**. Now queuing and shuffling songs...")

            queue = get_queue(interaction.guild_id)
            song_list = []
            
            # The entries are flat, so we need to re-extract each one to get a streamable URL
            with yt_dlp.YoutubeDL(ydl_extract_options) as ydl_extract:
                # Limit to first 50 songs to avoid long waits
                for entry in search_result['entries'][:50]:
                    try:
                        # Get the title from the initial flat search, which is more reliable.
                        title = entry.get('title')
                        if not title or '[Deleted video]' in title or '[Private video]' in title:
                            continue # Skip deleted or private videos

                        # Now, just extract the info needed to get the streamable URL.
                        entry_info = ydl_extract.extract_info(entry['url'], download=False)
                        audio_url = entry_info["url"]
                        
                        song_list.append((audio_url, title))
                    except Exception as e:
                        print(f"Couldn't queue '{entry.get('title', 'a video')}': {e}")
                        pass 

            if not song_list:
                await interaction.followup.send(f"Could not queue any songs from **{playlist_title}**.", ephemeral=True)
                return

            random.shuffle(song_list)
            for song in song_list:
                queue.append(song)
            
            await interaction.followup.send(f"Queued {len(song_list)} songs from **{playlist_title}** and shuffled them!")
            
            voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
            if not voice_client or not voice_client.is_connected():
                voice_client = await voice_channel.connect()
            
            if not voice_client.is_playing() and not voice_client.is_paused():
                await play_next_song(voice_client, interaction.guild_id, interaction.channel)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

@bot.tree.command(name="queue", description="Display the current song queue")
async def queue_command(interaction: discord.Interaction):
    queue = get_queue(interaction.guild_id)
    if not queue:
        await interaction.response.send_message("The queue is empty.", ephemeral=True)
        return

    embed = discord.Embed(title="Song Queue", color=discord.Color.blue())
    queue_text = ""
    
    now_playing_title = NOW_PLAYING.get(interaction.guild_id)
    if now_playing_title:
        embed.add_field(name="Now Playing", value=now_playing_title, inline=False)

    for i, (url, title) in enumerate(queue):
        queue_text += f"{i+1}. {title}\n"
    
    if not queue_text:
        queue_text = "The queue is empty."

    embed.description = queue_text
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="etla3", description="Disconnect the bot from the voice channel")
async def etla3_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    guild_id = interaction.guild_id
    if guild_id in DISCONNECT_TASKS:
        DISCONNECT_TASKS[guild_id].cancel()
        del DISCONNECT_TASKS[guild_id]

    if voice_client and voice_client.is_connected():
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            
        await voice_client.disconnect()
        
        if guild_id in SONG_QUEUES:
            del SONG_QUEUES[guild_id]
        if guild_id in NOW_PLAYING:
            del NOW_PLAYING[guild_id]
            
        await interaction.followup.send("Disconnected and cleared the queue.")
    else:
        await interaction.followup.send("I am not in a voice channel.")

# Run the bot
if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in .env file") 