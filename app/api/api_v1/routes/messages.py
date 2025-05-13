import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# Import the ConnectionManager
from app import sockets

router = APIRouter()


@router.websocket("/open")
async def websocket_endpoint(websocket: WebSocket):
    # IMPORTANT: Accept the connection immediately
    await websocket.accept()

    user_id: int | None = None
    try:
        # Wait for the initial connection message
        initial_data = await websocket.receive_text()
        try:
            initial_message = json.loads(initial_data)
        except json.JSONDecodeError:
            await websocket.send_json(
                {"msg": "error", "details": "Invalid JSON format"}
            )
            await websocket.close()
            return

        # Validate connection message
        if initial_message.get("msg") != "connect" or "user_id" not in initial_message:
            await websocket.send_json(
                {"msg": "error", "details": "Invalid connection message"}
            )
            await websocket.close()
            return

        # Extract user_id and connect via manager
        user_id = initial_message["user_id"]
        await sockets.manager.connect(websocket, user_id)

        # Send connection confirmation
        await websocket.send_json({"msg": "connected", "user_id": user_id})

        # Ping-pong mechanism to keep connection alive
        while True:
            try:
                # Wait for a message with a timeout
                message_data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=30.0
                )

                try:
                    message = json.loads(message_data)
                except json.JSONDecodeError:
                    await websocket.send_json(
                        {"msg": "error", "details": "Invalid JSON format"}
                    )
                    continue

                # Handle different message types
                if message.get("msg") == "ping":
                    await websocket.send_json({"msg": "pong"})
                else:
                    # Echo or process other messages
                    await websocket.send_json({"msg": "echo", "data": message})

            except asyncio.TimeoutError:
                # Send a ping to check connection
                try:
                    await sockets.manager.ping(websocket)
                    # Wait for pong
                    pong_result = await sockets.manager.pong(websocket)
                    if not pong_result:
                        break
                except Exception:
                    break

    except WebSocketDisconnect:
        print(f"Client {user_id} disconnected")
    except Exception as e:
        print(f"Unexpected error in WebSocket: {e}")
    finally:
        # Ensure disconnection is handled
        if user_id is not None:
            sockets.manager.disconnect(user_id)
