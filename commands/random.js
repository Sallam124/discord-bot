module.exports = {
  name: 'random',
  description: 'Shuffle the queue randomly',
  async execute(message, args, client) {
    const queue = client.distube.getQueue(message);
    if (!queue) return message.reply('Nothing is playing!');
    queue.shuffle();
    message.react('🔀');
  }
}; 