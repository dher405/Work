// server.js
import express from 'express';
import http from 'http';
import { WebSocketServer } from 'ws';

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: '/ws' });

// Optional: HTTP endpoint just to confirm it's alive
app.get('/', (req, res) => {
  res.send('WebSocket backend is running ✅');
});

wss.on('connection', (ws) => {
  console.log('🔌 New WebSocket connection');

  ws.on('message', (message) => {
    console.log('📨 Received:', message.toString());
    // Echo message back
    ws.send(`🪞 Echo: ${message}`);
  });

  ws.on('close', () => {
    console.log('🔌 WebSocket disconnected');
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`🚀 WebSocket server listening on port ${PORT}`);
});
