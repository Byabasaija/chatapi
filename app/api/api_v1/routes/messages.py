import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from app.api.deps import get_db
from app.services.message import handle_incoming_message
from app.sockets.manager import manager

router = APIRouter()


@router.websocket("/open")
async def websocket_endpoint(websocket: WebSocket, session: Session = Depends(get_db)):
    await websocket.accept()

    user_id: int | None = None
    try:
        initial_data = await websocket.receive_text()
        try:
            initial_message = json.loads(initial_data)
        except json.JSONDecodeError:
            await websocket.send_json(
                {"msg": "error", "details": "Invalid JSON format"}
            )
            await websocket.close()
            return

        if initial_message.get("msg") != "connect" or "user_id" not in initial_message:
            await websocket.send_json(
                {"msg": "error", "details": "Invalid connection message"}
            )
            await websocket.close()
            return

        user_id = initial_message["user_id"]
        await manager.connect(websocket, user_id)

        await websocket.send_json({"msg": "connected", "user_id": user_id})

        while True:
            message_data = await manager.get_message(user_id, timeout=30.0)
            if message_data is None:
                # Timeout -> send ping
                await manager.ping(user_id)
                continue

            try:
                message = json.loads(message_data)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"msg": "error", "details": "Invalid JSON format"}
                )
                continue

            if message.get("msg") == "ping":
                await websocket.send_json({"msg": "pong"})
            elif message.get("msg") == "pong":
                # Ignore or log
                continue
            elif message.get("msg") == "message":
                await handle_incoming_message(session, message)

            else:
                await websocket.send_json({"msg": "echo", "data": message})

    except WebSocketDisconnect:
        print(f"Client {user_id} disconnected")
    except Exception as e:
        print(f"Unexpected error in WebSocket: {e}")
    finally:
        if user_id is not None:
            manager.disconnect(user_id)
