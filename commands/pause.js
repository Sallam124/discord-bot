module.exports = {
  name: 'pause',
  description: 'Pause the current track',
  async execute(message, args, client) {
    const queue = client.distube.getQueue(message);
    if (!queue) return message.reply('Nothing is playing!');
    queue.pause();
    message.react('⏸️');
  }
}; 