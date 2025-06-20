module.exports = {
  name: 'spotify-login',
  description: 'Get a personalized Spotify OAuth login URL',
  async execute(message, args, client) {
    // Replace with your actual public domain
    const publicDomain = 'https://your-public-domain.com';
    const userId = message.author.id;
    const loginUrl = `${publicDomain}/login?userId=${userId}`;
    message.reply(`Here is your Spotify login link: ${loginUrl}`);
  }
}; 