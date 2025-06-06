import asyncio
import logging
import json
import random
import ssl
import requests
import websockets
from aiortc import RTCPeerConnection, RTCIceServer, RTCConfiguration

# Configuration
ice_servers = [
    ice_servers = [
    RTCIceServer(urls="stun:stun.l.google.com:19302"),  # STUN (May not work on Render)
    RTCIceServer(urls="turn:relay.metered.ca:80", username="open", credential="open")  # Public TURN
    ]
]


WS_SERVER_BASE = "wss://wcm-ev-p02-eo1.engage.ringcentral.com:8080"
ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiJ9.eyJhZ250IjpbMTUyOTg2XSwiYWdudC1hY2MiOnsiMTUyOTg2IjoiMjEyNzAwMDEifSwiZW1iZCI6ZmFsc2UsInJjYWMiOiIzNzQzOTUxMCIsImVzdSI6ZmFsc2UsImxhcHAiOiJTU08iLCJmbHIiOmZhbHNlLCJzc28iOnRydWUsInJjaWQiOjE5MTgwOTYwMDgsInBsYXQiOiJldi1wMDIiLCJhY2N0IjoiMjEyNzAwMDAiLCJleHAiOjE3NDIxODA5Nzl9.BCX5N73WAsmQZrHR4JyTWO-0g8wvujFy0haQZdXycoGjcfDL0OnFltvTNsewUhN3_camJv2zw1yNvCYB095GxocZNhFhRi5JFk-fQqsxVtctgqp1xeKM_OkQQb-3Fghblp2ss0KlrymzMyB7Yo3Io_rUAmlMwSzhoCKU1B2KffwWNnYGzRUfw79n_VIw_4tAub0nzbhYqumdUDz-9uGuk2Bb8F7rgw_vAkkYicoQncCI52pPQlV-dIktRcnQIVnnHsLigUvBmyAHKdVkjcapkSqTwNfdBLSenCxZ2i166j5-O63bIivjHSxjOVdH9fiCxgl3MDwai0Kmtilgv-KcwA";
AGENT_ID = "152986"
CLIENT_REQUEST_ID = "EAG:08415eb6-311a-7639-ad11-d6f25746aa36"

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("STUN_WS_Test")

# Function to perform DTLS handshake
async def perform_dtls_handshake():
    logger.info("Attempting DTLS handshake before STUN...")

    try:
        ice_servers = [RTCIceServer(urls="stun:stun.l.google.com:19302")]
        pc = RTCPeerConnection(RTCConfiguration(iceServers=ice_servers))

        pc.createDataChannel("test")

        @pc.on("icecandidate")
        async def on_ice_candidate(candidate):
            if candidate:
                logger.info(f"🔍 Found ICE Candidate: {candidate}")

        @pc.on("iceconnectionstatechange")
        async def on_ice_connection_state_change():
            logger.info(f"🔄 ICE Connection State: {pc.iceConnectionState}")

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        # ✅ Wait for ICE Gathering to Complete
        await asyncio.sleep(5)

        if pc.iceConnectionState == "failed":
            logger.error("❌ ICE Candidate Gathering Failed! STUN might be blocked.")
            return None

        logger.info("✅ DTLS handshake successful.")
        return pc

    except Exception as e:
        logger.error(f"❌ DTLS handshake failed: {e}")
        return None


# Function to establish STUN connection and retrieve external IP & port
async def setup_stun(pc):
    logger.info("🔍 Attempting to set up STUN connection...")
    stun_success = False
    external_ip, external_port = None, None

    async def ice_callback(candidate):
        nonlocal stun_success, external_ip, external_port
        if candidate:
            ip_match = candidate.candidate.split()[4]
            port_match = candidate.candidate.split()[5]
            if ip_match and port_match:
                external_ip = ip_match
                external_port = int(port_match)
                stun_success = True
                logger.info(f"✅ STUN Resolved External IP: {external_ip}, Port: {external_port}")
                await connect_websocket(external_ip, external_port)

    pc.on_ice_candidate = ice_callback

    await asyncio.sleep(3)  # Give time for STUN gathering

    if not stun_success:
        logger.error("❌ STUN connection failed.")
        return None, None

    return external_ip, external_port

# Function to capture API request and response for WebSocket
def capture_websocket_api():
    ws_url = f"{WS_SERVER_BASE}/?access_token={ACCESS_TOKEN}&agent_id={AGENT_ID}&x-engage-client-request-id={CLIENT_REQUEST_ID}"

    headers = {
        "Host": "wcm-ev-p02-eo1.engage.ringcentral.com:8080",
        "Connection": "Upgrade",
        "Upgrade": "websocket",
        "Origin": "https://ringcx.ringcentral.com",
        "Sec-WebSocket-Version": "13",
        "Sec-WebSocket-Key": str(random.randint(1, 1000000)),
        "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(ws_url, headers=headers, timeout=5)
        logger.info("📡 WebSocket API Request Sent")
        logger.info(f"🔍 Request Headers: {json.dumps(headers, indent=2)}")
        logger.info(f"🟢 Response Code: {response.status_code}")
        logger.info(f"📩 Response Headers: {json.dumps(dict(response.headers), indent=2)}")
    except Exception as e:
        logger.error(f"❌ Failed to capture WebSocket API request: {e}")

# Function to establish WebSocket connection
async def connect_websocket(ip, port):
    logger.info(f"🌍 Attempting WebSocket connection to {WS_SERVER_BASE} from {ip}:{port}...")

    ws_url = f"{WS_SERVER_BASE}/?access_token={ACCESS_TOKEN}&agent_id={AGENT_ID}&x-engage-client-request-id={CLIENT_REQUEST_ID}"

    headers = {
        "Host": "wcm-ev-p02-eo1.engage.ringcentral.com:8080",
        "Connection": "Upgrade",
        "Upgrade": "websocket",
        "Origin": "https://ringcx.ringcentral.com",
        "Sec-WebSocket-Version": "13",
        "Sec-WebSocket-Key": str(random.randint(1, 1000000)),
        "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }

    # Capture API request and response details before WebSocket connection
    capture_websocket_api()

    try:
        async with websockets.connect(ws_url, extra_headers=headers, ssl=ssl.create_default_context()) as ws:
            logger.info("✅ WebSocket connection established!")
            await ws.send("PING")
            await send_test_udp_packets(ws)
            async for message in ws:
                logger.info(f"📩 WebSocket Response: {message}")
    except Exception as e:
        logger.error(f"❌ WebSocket connection failed: {e}")

# Function to send test UDP packets over WebSocket
async def send_test_udp_packets(ws):
    logger.info("📡 Sending test UDP packets over WebSocket...")
    test_message = json.dumps({"type": "test", "message": "Hello from UDP over WebSocket!"})
    await ws.send(test_message)

# Main function to coordinate DTLS, STUN, and WebSocket
async def main():
    logger.info("🚀 Starting STUN & WebSocket Test...")
    
    pc = await perform_dtls_handshake()
    if not pc:
        logger.error("❌ DTLS failed. Stopping test.")
        return
    
    ip, port = await setup_stun(pc)
    if not ip or not port:
        logger.error("❌ STUN failed. Skipping WebSocket connection.")
        return

    await connect_websocket(ip, port)

# Run the async event loop
if __name__ == "__main__":
    asyncio.run(main())
