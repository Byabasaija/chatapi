import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
        self.message_queues: dict[int, asyncio.Queue] = {}
        self.receive_tasks: dict[int, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        self.active_connections[user_id] = websocket
        self.message_queues[user_id] = asyncio.Queue()
        self.receive_tasks[user_id] = asyncio.create_task(
            self._receive_loop(user_id, websocket)
        )

    def disconnect(self, user_id: int):
        if user_id in self.receive_tasks:
            self.receive_tasks[user_id].cancel()
        self.active_connections.pop(user_id, None)
        self.message_queues.pop(user_id, None)
        self.receive_tasks.pop(user_id, None)

    def get_ws(self, user_id: int) -> WebSocket | None:
        return self.active_connections.get(user_id)

    async def send_message(self, data: dict):
        recipient_id = data["recipient_id"]
        sender_id = data["sender_id"]
        websocket = self.get_ws(recipient_id)
        data = {
            "content": data.get("content"),
            "encrypted_payload": data.get("encrypted_payload"),
            "content_type": data.get("content_type"),
            "sender_id": data.get("sender_id"),
        }
        message = {
            "msg": "message",
            "data": data,
        }
        if websocket:
            await websocket.send_json(message)
            return True
        else:
            self.send_acknowledgment(
                data,
                sender_id,
            )
            return False

    async def send_acknowledgment(self, data: str, sender_id: int):
        websocket = self.get_ws(sender_id)
        if websocket:
            await websocket.send_json(
                {
                    "msg": "delivered",
                    "data": data,
                }
            )
            return True
        return False

    async def _receive_loop(self, user_id: int, websocket: WebSocket):
        try:
            while True:
                msg = await websocket.receive_text()
                await self.message_queues[user_id].put(msg)
        except Exception:
            # When disconnected or errored
            self.disconnect(user_id)

    async def get_message(self, user_id: int, timeout: float = 30.0) -> str | None:
        queue = self.message_queues.get(user_id)
        if queue:
            try:
                return await asyncio.wait_for(queue.get(), timeout=timeout)
            except asyncio.TimeoutError:
                return None
        return None

    async def ping(self, user_id: int):
        websocket = self.get_ws(user_id)
        if websocket:
            await websocket.send_json({"msg": "ping"})


manager = ConnectionManager()
