# Importing libraries and modules
import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import wavelink
import asyncio

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youtubepass")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", 2333))
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "localhost")

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
    # Connect to Lavalink
    if not hasattr(bot, 'wavelink_node'):  # Prevent double connection
        node: wavelink.Node = await wavelink.NodePool.create_node(
            bot=bot,
            host=LAVALINK_HOST,
            port=LAVALINK_PORT,
            password=LAVALINK_PASSWORD,
            https=False
        )
        bot.wavelink_node = node
    bot.add_view(MusicControlPanel())


@bot.tree.command(name="skip", description="Skips the current playing song")
async def skip(interaction: discord.Interaction):
    try:
        player: wavelink.Player = interaction.guild.voice_client
        if player and (player.is_playing() or player.is_paused()):
            await player.stop()
            await interaction.response.send_message("Skipped the current song.")
        else:
            await interaction.response.send_message("Not playing anything to skip.")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")


@bot.tree.command(name="pause", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction):
    try:
        player: wavelink.Player = interaction.guild.voice_client
        if player is None:
            return await interaction.response.send_message("I'm not in a voice channel.")
        if not player.is_playing():
            return await interaction.response.send_message("Nothing is currently playing.")
        await player.pause()
        await interaction.response.send_message("Playback paused!")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")


@bot.tree.command(name="resume", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction):
    try:
        player: wavelink.Player = interaction.guild.voice_client
        if player is None:
            return await interaction.response.send_message("I'm not in a voice channel.")
        if not player.is_paused():
            return await interaction.response.send_message("I'm not paused right now.")
        await player.resume()
        await interaction.response.send_message("Playback resumed!")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")


@bot.tree.command(name="stop", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    try:
        player: wavelink.Player = interaction.guild.voice_client
        if not player or not player.is_connected():
            return await interaction.response.send_message("I'm not connected to any voice channel.")
        guild_id_str = str(interaction.guild_id)
        if guild_id_str in SONG_QUEUES:
            SONG_QUEUES[guild_id_str].clear()
        if player.is_playing() or player.is_paused():
            await player.stop()
        await player.disconnect()
        await interaction.response.send_message("Stopped playback and disconnected!")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {e}")


@bot.tree.command(name="play", description="Play a song or add it to the queue.")
@app_commands.describe(song_query="Search query or URL")
async def play(interaction: discord.Interaction, song_query: str):
    try:
        await interaction.response.defer()
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("You must be in a voice channel to use this command.")
            return
        channel = interaction.user.voice.channel
        player: wavelink.Player = interaction.guild.voice_client
        if player is None:
            player = await channel.connect(cls=wavelink.Player)
        elif player.channel != channel:
            await player.move_to(channel)
        # Search for track
        try:
            tracks = await wavelink.YouTubeTrack.search(song_query, return_first=False)
        except Exception as e:
            await interaction.followup.send(f"Error searching for track: {e}")
            return
        if not tracks:
            await interaction.followup.send("No results found.")
            return
        track = tracks[0]
        await player.play(track)
        await interaction.followup.send(f"Now playing: **{track.title}**")
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")


async def play_next_song(player, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title = SONG_QUEUES[guild_id].popleft()

        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k",
            # Remove executable if FFmpeg is in PATH
        }

        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="bin\\ffmpeg\\ffmpeg.exe")

        def after_play(error):
            if error:
                print(f"Error playing {title}: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(player, guild_id, channel), bot.loop)

        player.play(source, after=after_play)
        asyncio.create_task(channel.send(f"Now playing: **{title}**"))
    else:
        await player.disconnect()
        SONG_QUEUES[guild_id] = deque()


class MusicControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.primary, custom_id="pause_button")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player and player.is_playing():
            await player.pause()
            await interaction.response.send_message("Playback paused!", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is currently playing.", ephemeral=True)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.success, custom_id="resume_button")
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player and player.is_paused():
            await player.resume()
            await interaction.response.send_message("Playback resumed!", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is paused.", ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, custom_id="skip_button")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player and (player.is_playing() or player.is_paused()):
            await player.stop()
            await interaction.response.send_message("Skipped the current song.", ephemeral=True)
        else:
            await interaction.response.send_message("Not playing anything to skip.", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, custom_id="stop_button")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        player: wavelink.Player = interaction.guild.voice_client
        if player and player.is_connected():
            await player.disconnect()
            await interaction.response.send_message("Stopped playback and disconnected!", ephemeral=True)
        else:
            await interaction.response.send_message("I'm not connected to any voice channel.", ephemeral=True)


@bot.tree.command(name="panel", description="Show the music control panel with buttons.")
async def panel(interaction: discord.Interaction):
    await interaction.response.send_message("Music Control Panel:", view=MusicControlPanel(), ephemeral=False)


# Run the bot
bot.run(TOKEN)