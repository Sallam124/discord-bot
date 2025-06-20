module.exports = {
  name: 'skip',
  description: 'Skip the current song',
  async execute(message, args, client) {
    const queue = client.distube.getQueue(message);
    if (!queue) return message.reply('There is nothing playing!');
    try {
      await queue.skip();
      message.react('⏭️');
    } catch (err) {
      message.reply('No more songs to skip!');
    }
  }
}; 