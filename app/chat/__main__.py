from math import log
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import jwt
import time
import logging
from typing import List
import aiohttp
from chat.settings import settings

import uvicorn

from pydantic import BaseModel

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


class Message(BaseModel):
    message: str
    user_id: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

manager = ConnectionManager()


def generate_centrifugo_token(user_id: str):
    token = jwt.encode({"sub": user_id, "exp": int(time.time()) + 10*60}, settings.centrifugo_secret, algorithm="HS256")
    print(f"userid: {user_id}, token: {token}")
    return token


async def publish_to_centrifugo(channel: str, data: dict):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"apikey {settings.centrifugo_api_key}"
    }
    payload = {
        "method": "publish",
        "params": {
            "channel": channel, 
            "data": data
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{settings.centrifugo_url}/api", 
            json=payload, 
            headers=headers
        ) as resp:
            return await resp.json()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    user_id = "user_" + str(int(time.time()))  # Simple user ID generation
    token = generate_centrifugo_token(user_id)
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "centrifugo_url": settings.centrifugo_socket_url,
            "centrifugo_token": token,
            "channel": settings.centrifugo_channel,
            "user_id": user_id
        }
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast message to all clients
            for connection in manager.active_connections:
                await connection.send_text(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/send")
async def send_message(msg: Message):
    data = {
        "user_id": msg.user_id,
        "text": msg.message,
        "timestamp": int(time.time())
    }
    await publish_to_centrifugo(settings.centrifugo_channel, data)
    return {"status": "ok"}


if __name__ == "__main__":
    log_format = "%(levelname)s:     %(message)s"
    logging.basicConfig(
        level=settings.log_level,
        format=log_format,
    )
    logging.info("APP start ✅, listening on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
