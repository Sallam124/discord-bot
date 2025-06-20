module.exports = {
  name: 'stop',
  description: 'Stop playback and clear the queue',
  async execute(message, args, client) {
    const queue = client.distube.getQueue(message);
    if (!queue) return message.reply('Nothing is playing!');
    await queue.stop();
    message.react('⏹️');
  }
}; 