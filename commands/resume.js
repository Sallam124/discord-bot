module.exports = {
  name: 'resume',
  description: 'Resume paused track',
  async execute(message, args, client) {
    const queue = client.distube.getQueue(message);
    if (!queue) return message.reply('Nothing is playing!');
    queue.resume();
    message.react('▶️');
  }
}; 