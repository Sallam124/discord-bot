const { QueryType } = require('distube');
const { getSpotifyTrackQuery } = require('../utils/spotifyHelper');

module.exports = {
  name: 'play',
  description: 'Play a song from YouTube, Spotify, or search keywords',
  async execute(message, args, client) {
    // Check if user is in a voice channel
    const voiceChannel = message.member.voice.channel;
    if (!voiceChannel) return message.reply('You need to be in a voice channel to play music!');
    if (!args.length) return message.reply('Please provide a YouTube/Spotify link or search keywords.');

    let query = args.join(' ');
    // If Spotify URL, extract metadata and search YouTube
    if (/open\.spotify\.com\//.test(query)) {
      try {
        query = await getSpotifyTrackQuery(query);
        if (!query) return message.reply('Could not extract track info from Spotify link.');
      } catch (err) {
        return message.reply('Error processing Spotify link.');
      }
    }

    // Play the song using DisTube
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