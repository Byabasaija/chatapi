import asyncio

from fastapi import WebSocket


class ConnectionManager:
    # INITIALIZE THE LIST AND CONNECTION
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    # CONNECT TO WEBSOCKET AND APPEND TO THE LIST
    async def connect(self, websocket: WebSocket, user_id: int):
        self.active_connections[user_id] = websocket

    # PURGE WEBSOCKET LIST STORE
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    # Fetch WebSocket and return them if it exists.
    def get_ws(self, user_id: int) -> WebSocket | None:
        return self.active_connections.get(user_id)

    # SEND MESSAGE AFTER WEBSOCKET IS ALIVE
    async def send_message(self, message: dict):
        user_ws = self.get_ws(message["user_id"])
        if user_ws is not None:
            websocket: WebSocket = user_ws
            await websocket.send_json(message)
            return True
        return False

    # Keep the WebSocket alive.
    async def ping(self, websocket: WebSocket):
        await websocket.send_json({"msg": "ping"})

    # Listening to the Websocket and sending message.
    async def pong(self, websocket: WebSocket):
        pong = await asyncio.wait_for(websocket.receive_text(), timeout=5)
        return pong == "pong"

    # Send a retry message to a user WebSocket
    # async def personal_notification(self, message: dict):
    #     connection_check = self.get_ws(message["message"]["user_id"])
    #     if connection_check:
    #         connection_check: WebSocket
    #         await connection_check.send_json(message)
    #         await asyncio.sleep(2)
    #         return True
    #     else:
    #         del self.active_connections[message["message"]["user_id"]]
    #         return False

    # def sanitize_data_request(self, data: any) -> any:
    #     # Putting here for want of a better place
    #     if isinstance(data, (list, tuple, set)):
    #         return type(data)(
    #             self.sanitize_data_request(x) for x in data if x or isinstance(x, bool)
    #         )
    #     elif isinstance(data, dict):
    #         return type(data)(
    #             (self.sanitize_data_request(k), self.sanitize_data_request(v))
    #             for k, v in data.items()
    #             if k and v or isinstance(v, bool)
    #         )
    #     else:
    #         return data


manager = ConnectionManager()
