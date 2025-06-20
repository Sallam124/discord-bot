const config = require('../config.json');

module.exports = {
  name: 'messageCreate',
  async execute(message, client) {
    // Ignore messages from bots or without prefix
    if (message.author.bot || !message.content.startsWith(config.prefix)) return;

    // Parse command and arguments
    const args = message.content.slice(config.prefix.length).trim().split(/ +/);
    const commandName = args.shift().toLowerCase();
    const command = client.commands.get(commandName);
    if (!command) return message.reply('Unknown command!');

    try {
      await command.execute(message, args, client);
    } catch (error) {
      console.error(error);
      message.reply('There was an error executing that command.');
    }
  }
}; 