const express = require('express');
const app = express();
const port = 8888;

app.get('/callback', (req, res) => {
  const code = req.query.code;
  console.log('Authorization code:', code);
  res.send('Authorization code received! You can close this tab.');
});

app.listen(port, () => {
  console.log(`Listening on http://localhost:${port}`);
});
