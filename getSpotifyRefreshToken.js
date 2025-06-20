require('dotenv').config();

const SpotifyWebApi = require('spotify-web-api-node');
const readline = require('readline');

const clientId = process.env.SPOTIFY_CLIENT_ID;
const clientSecret = process.env.SPOTIFY_CLIENT_SECRET;
const redirectUri = process.env.SPOTIFY_REDIRECT_URI;

const spotifyApi = new SpotifyWebApi({ clientId, clientSecret, redirectUri });

// Scopes required for your app
const scopes = [
  'user-read-private',
  'user-read-email',
  'playlist-read-private',
  'user-library-read',
];

const authorizeURL = spotifyApi.createAuthorizeURL(scopes, 'state');

console.log('1. Go to this URL in your browser and authorize the app:');
console.log(authorizeURL);
console.log('\n2. After authorization, you will be redirected to your redirect URI.');
console.log('Copy the "code" parameter from the URL (after "?code=") and paste it below.\n');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

rl.question('Paste the code here: ', async (code) => {
  try {
    const data = await spotifyApi.authorizationCodeGrant(code.trim());
    console.log('\nSuccess! Here is your refresh token:');
    console.log(data.body['refresh_token']);
  } catch (err) {
    console.error('Error getting tokens:', err.message || err);
  }
  rl.close();
});
