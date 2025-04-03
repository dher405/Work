import WebSocket from 'ws';

const agentId = '152986';
const accessToken = 'eyJhbGciOiJSUzI1NiJ9....'; // Paste full token here
const requestId = 'EAG:23a5760a-5bb8-cab6-b013-a29b0a129209';

const wsUrl = `wss://wcm-ev-p02-eo1.engage.ringcentral.com:8080/?access_token=${encodeURIComponent(accessToken)}&agent_id=${agentId}&x-engage-client-request-id=${encodeURIComponent(requestId)}`;
console.log("🔌 Connecting to:", wsUrl);

const socket = new WebSocket(wsUrl);

socket.on('open', () => {
  console.log("✅ IQ WebSocket connected.");

  const loginPayload = {
    ui_request: {
      "@destination": "IQ",
      "@type": "LOGIN-PHASE-1",
      "@message_id": "2562253c-ae7f-a025-1a2f-7727a95dd675",
      response_to: "",
      reconnect: { "#text": "" },
      agent_id: { "#text": agentId },
      access_token: { "#text": accessToken }
    }
  };

  socket.send(JSON.stringify(loginPayload));
  console.log("📨 Sent LOGIN-PHASE-1");
});

socket.on('message', (data) => {
  console.log("📩 Received:", data.toString());
});

socket.on('error', (err) => {
  console.error("❌ IQ WebSocket error:", err.message);
});

socket.on('close', (code, reason) => {
  console.warn(`🔌 IQ WebSocket closed. Code: ${code}, Reason: ${reason}`);
});
