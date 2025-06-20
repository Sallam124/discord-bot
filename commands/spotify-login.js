module.exports = {
  name: 'spotify-login',
  description: 'Get a personalized Spotify OAuth login URL',
  async execute(message, args, client) {
    const publicDomain = process.env.PUBLIC_DOMAIN;
    const userId = message.author.id;
    const loginUrl = `${publicDomain}/login?userId=${userId}`;
    message.reply(`Here is your Spotify login link: ${loginUrl}`);
  }
}; 