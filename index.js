require('dotenv').config();
const { Client, GatewayIntentBits, REST, Routes, SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, AudioPlayerStatus, NoSubscriberBehavior, getVoiceConnection } = require('@discordjs/voice');
const ytdl = require('ytdl-core');
const ffmpeg = require('@ffmpeg-installer/ffmpeg');
const { spawn } = require('child_process');
const ytSearch = require('yt-search');

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.MessageContent
  ]
});

// Song queue per guild
const queues = new Map();

const commands = [
  new SlashCommandBuilder()
    .setName('play')
    .setDescription('Play a song from YouTube (link or search)')
    .addStringOption(option =>
      option.setName('query')
        .setDescription('YouTube link or search keywords')
        .setRequired(true)
    ),
  new SlashCommandBuilder()
    .setName('pause')
    .setDescription('Pause the current song'),
  new SlashCommandBuilder()
    .setName('resume')
    .setDescription('Resume playback'),
  new SlashCommandBuilder()
    .setName('skip')
    .setDescription('Skip the current song'),
  new SlashCommandBuilder()
    .setName('queue')
    .setDescription('Show the current queue'),
  new SlashCommandBuilder()
    .setName('leave')
    .setDescription('Leave the voice channel'),
].map(cmd => cmd.toJSON());

client.once('ready', async () => {
  console.log(`Logged in as ${client.user.tag}!`);
  // Register slash commands for all guilds the bot is in
  const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_TOKEN);
  const appId = client.user.id;
  const guilds = client.guilds.cache.map(guild => guild.id);
  for (const guildId of guilds) {
    await rest.put(Routes.applicationGuildCommands(appId, guildId), { body: commands });
  }
  console.log('Slash commands registered.');
});

function getQueue(guildId) {
  if (!queues.has(guildId)) queues.set(guildId, []);
  return queues.get(guildId);
}

async function playSong(interaction, voiceChannel, song) {
  const guildId = interaction.guildId;
  let connection = getVoiceConnection(guildId);
  if (!connection) {
    connection = joinVoiceChannel({
      channelId: voiceChannel.id,
      guildId: voiceChannel.guild.id,
      adapterCreator: voiceChannel.guild.voiceAdapterCreator,
    });
  }
  let queue = getQueue(guildId);
  queue.push(song);
  if (queue.length > 1) {
    await interaction.reply(`Queued: **${song.title}**`);
    return;
  }
  await interaction.reply(`Now playing: **${song.title}**`);
  const player = createAudioPlayer({ behaviors: { noSubscriber: NoSubscriberBehavior.Pause } });
  connection.subscribe(player);
  const playNext = () => {
    queue = getQueue(guildId);
    if (queue.length === 0) {
      connection.destroy();
      return;
    }
    const nextSong = queue[0];
    const stream = ytdl(nextSong.url, { filter: 'audioonly', quality: 'highestaudio' });
    const resource = createAudioResource(stream);
    player.play(resource);
  };
  player.on(AudioPlayerStatus.Idle, () => {
    queue.shift();
    playNext();
  });
  playNext();
  connection.player = player;
}

client.on('interactionCreate', async (interaction) => {
  if (!interaction.isChatInputCommand()) return;
  const guildId = interaction.guildId;
  const member = interaction.member;
  const voiceChannel = member.voice.channel;
  const queue = getQueue(guildId);

  if (interaction.commandName === 'play') {
    const query = interaction.options.getString('query');
    let songInfo;
    if (ytdl.validateURL(query)) {
      const info = await ytdl.getInfo(query);
      songInfo = { title: info.videoDetails.title, url: info.videoDetails.video_url };
    } else {
      // Search YouTube
      const result = await ytSearch(query);
      if (!result.videos.length) {
        await interaction.reply({ content: 'No results found on YouTube.', ephemeral: true });
        return;
      }
      const video = result.videos[0];
      songInfo = { title: video.title, url: video.url };
    }
    if (!voiceChannel) {
      await interaction.reply({ content: 'You need to be in a voice channel!', ephemeral: true });
      return;
    }
    playSong(interaction, voiceChannel, songInfo);
  }

  if (interaction.commandName === 'pause') {
    const connection = getVoiceConnection(guildId);
    if (!connection || !connection.player) {
      await interaction.reply({ content: 'Nothing is playing.', ephemeral: true });
      return;
    }
    connection.player.pause();
    await interaction.reply('Paused.');
  }

  if (interaction.commandName === 'resume') {
    const connection = getVoiceConnection(guildId);
    if (!connection || !connection.player) {
      await interaction.reply({ content: 'Nothing is playing.', ephemeral: true });
      return;
    }
    connection.player.unpause();
    await interaction.reply('Resumed.');
  }

  if (interaction.commandName === 'skip') {
    const connection = getVoiceConnection(guildId);
    if (!connection || !connection.player) {
      await interaction.reply({ content: 'Nothing is playing.', ephemeral: true });
      return;
    }
    connection.player.stop();
    await interaction.reply('Skipped.');
  }

  if (interaction.commandName === 'queue') {
    if (!queue.length) {
      await interaction.reply('The queue is empty.');
      return;
    }
    const embed = new EmbedBuilder()
      .setTitle('Current Queue')
      .setDescription(queue.map((s, i) => `${i === 0 ? '**Now Playing:**' : `${i}.`} ${s.title}`).join('\n'));
    await interaction.reply({ embeds: [embed] });
  }

  if (interaction.commandName === 'leave') {
    const connection = getVoiceConnection(guildId);
    if (connection) {
      connection.destroy();
      queues.set(guildId, []);
      await interaction.reply('Left the voice channel and cleared the queue.');
    } else {
      await interaction.reply({ content: 'I am not in a voice channel.', ephemeral: true });
    }
  }
});

// The token has been hardcoded for testing. 
// For better security, move this to a .env file or Railway environment variables.
client.login('MTM4NTcwMjUyNjE5NTU5NzM1Mg.GBq_KE.yX2U9zwaLTsTrcnPrkZ_EsOt8lAI-zO_5IxE3g'); 