// Load environment variables from .env
require('dotenv').config();

// Import required libraries
const { Client, GatewayIntentBits, Collection } = require('discord.js');
const { DisTube } = require('distube');
const { SpotifyPlugin } = require('@distube/spotify');
const { join } = require('path');
const fs = require('fs');

// Load config
const config = require('./config.json');

// Create a new Discord client with necessary intents
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.MessageContent
  ]
});

// Initialize DisTube with Spotify plugin
client.distube = new DisTube(client, {
  plugins: [
    new SpotifyPlugin({
      emitEventsAfterFetching: true
    })
  ],
  leaveOnStop: config.options.leaveOnStop,
  leaveOnFinish: config.options.leaveOnFinish,
  leaveOnEmpty: config.options.leaveOnEmpty
});

// Command collection
client.commands = new Collection();

// Dynamically load command files
const commandFiles = fs.readdirSync(join(__dirname, 'commands')).filter(file => file.endsWith('.js'));
for (const file of commandFiles) {
  const command = require(`./commands/${file}`);
  client.commands.set(command.name, command);
}

// Dynamically load event files
const eventFiles = fs.readdirSync(join(__dirname, 'events')).filter(file => file.endsWith('.js'));
for (const file of eventFiles) {
  const event = require(`./events/${file}`);
  if (event.once) {
    client.once(event.name, (...args) => event.execute(...args, client));
  } else {
    client.on(event.name, (...args) => event.execute(...args, client));
  }
}

// Login to Discord
client.login(process.env.DISCORD_TOKEN); 