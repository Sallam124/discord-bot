module.exports = {
  name: 'quit',
  description: 'Alias for leave command',
  async execute(message, args, client) {
    const leave = require('./leave');
    await leave.execute(message, args, client);
  }
}; 