module.exports = {
  name: 'queue',
  description: 'Show the current music queue',
  async execute(message, args, client) {
    const queue = client.distube.getQueue(message);
    if (!queue) return message.reply('Queue is empty!');
    const q = queue.songs
      .map((song, i) => `${i === 0 ? 'Now Playing:' : `${i}.`} ${song.name} [${song.formattedDuration}]`)
      .join('\n');
    message.channel.send('```' + q + '```');
  }
}; 