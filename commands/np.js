module.exports = {
  name: 'np',
  description: 'Show the currently playing track',
  async execute(message, args, client) {
    const queue = client.distube.getQueue(message);
    if (!queue || !queue.songs.length) return message.reply('Nothing is playing!');
    const song = queue.songs[0];
    message.channel.send(`Now playing: **${song.name}** [${song.formattedDuration}]\n${song.url}`);
  }
}; 