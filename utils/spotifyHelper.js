const SpotifyWebApi = require('spotify-web-api-node');

// Initialize Spotify API client
const spotifyApi = new SpotifyWebApi({
  clientId: process.env.SPOTIFY_CLIENT_ID,
  clientSecret: process.env.SPOTIFY_CLIENT_SECRET,
  refreshToken: process.env.SPOTIFY_REFRESH_TOKEN
});

// Refresh the access token
async function refreshAccessToken() {
  const data = await spotifyApi.refreshAccessToken();
  spotifyApi.setAccessToken(data.body['access_token']);
  if (!data.body['access_token']) {
    console.error('❌ Spotify access token is missing after refresh!');
  } else {
    console.log('✅ Spotify access token:', data.body['access_token']);
  }
}

// Extract track info from a Spotify URL and return a YouTube search query
async function getSpotifyTrackQuery(url) {
  await refreshAccessToken();
  const accessToken = spotifyApi.getAccessToken();
  if (!accessToken) {
    throw new Error('Spotify access token is undefined! Check your refresh token and credentials.');
  }
  let trackInfo;
  if (url.includes('/track/')) {
    // Single track
    const id = url.split('/track/')[1].split('?')[0];
    trackInfo = await spotifyApi.getTrack(id);
    const { name, artists } = trackInfo.body;
    return `${name} ${artists[0].name}`;
  } else if (url.includes('/playlist/')) {
    // Playlist (return first track as example)
    const id = url.split('/playlist/')[1].split('?')[0];
    const playlist = await spotifyApi.getPlaylist(id);
    const firstTrack = playlist.body.tracks.items[0].track;
    return `${firstTrack.name} ${firstTrack.artists[0].name}`;
  } else if (url.includes('/album/')) {
    // Album (return first track as example)
    const id = url.split('/album/')[1].split('?')[0];
    const album = await spotifyApi.getAlbum(id);
    const firstTrack = album.body.tracks.items[0];
    return `${firstTrack.name} ${firstTrack.artists[0].name}`;
  }
  return null;
}

module.exports = { getSpotifyTrackQuery }; 