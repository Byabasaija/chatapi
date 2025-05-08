from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ping")
async def websocket_ping(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Wait for a message from the client (e.g., ping)
            data = await websocket.receive_text()

            if data == "ping":
                # Send a pong response back to the client
                await websocket.send_text("pong")
            else:
                await websocket.send_text("Invalid message, expected 'ping'.")
    except WebSocketDisconnect:
        print("Client disconnected")
