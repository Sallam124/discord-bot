module.exports = {
  name: 'leave',
  description: 'Leave the voice channel',
  async execute(message, args, client) {
    const voiceChannel = message.member.voice.channel;
    if (!voiceChannel) return message.reply('You are not in a voice channel!');
    try {
      await voiceChannel.leave();
      message.react('👋');
    } catch (err) {
      message.reply('Failed to leave the channel.');
    }
  }
}; 