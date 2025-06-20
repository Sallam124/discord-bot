const { QueryType } = require('distube');

module.exports = {
  name: 'play',
  description: 'Play a song from YouTube or search keywords',
  async execute(message, args, client) {
    // Check if user is in a voice channel
    const voiceChannel = message.member.voice.channel;
    if (!voiceChannel) return message.reply('You need to be in a voice channel to play music!');
    if (!args.length) return message.reply('Please provide a YouTube link or search keywords.');

    let query = args.join(' ');

    // Play the song or playlist using DisTube
    try {
      await client.distube.play(voiceChannel, query, {
        member: message.member,
        textChannel: message.channel,
        message
      });
      message.react('🎶');
    } catch (err) {
      message.reply('Failed to play the track.');
    }
  }
}; 