import logging
import sqlite3
import time
from contextlib import asynccontextmanager

import aiohttp
import jwt
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from chat.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


class Message(BaseModel):
    message: str
    user_id: str


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)


manager = ConnectionManager()

DB_PATH = "chat_messages.db"


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_message(user_id: str, text: str, timestamp: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (user_id, text, timestamp) VALUES (?, ?, ?)",
        (user_id, text, timestamp),
    )
    conn.commit()
    conn.close()


def get_last_messages(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT user_id, text, timestamp FROM messages ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    # Возвращаем в обратном порядке (от старых к новым)
    return [{"user_id": row[0], "text": row[1], "timestamp": row[2]} for row in reversed(rows)]


def generate_centrifugo_token(user_id: str):
    return jwt.encode(
        {"sub": user_id, "exp": int(time.time()) + 10 * 60},
        settings.centrifugo_secret,
        algorithm="HS256",
    )


async def publish_to_centrifugo(channel: str, data: dict):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"apikey {settings.centrifugo_api_key}",
    }
    payload = {"method": "publish", "params": {"channel": channel, "data": data}}

    async with (
        aiohttp.ClientSession() as session,
        session.post(f"{settings.centrifugo_url}/api", json=payload, headers=headers) as resp,
    ):
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
            "user_id": user_id,
        },
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Broadcast message to all clients
            for connection in manager.active_connections:
                await connection.send_text(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/history")
async def get_history():
    return get_last_messages(500)


@app.post("/send")
async def send_message(msg: Message):
    data = {"user_id": msg.user_id, "text": msg.message, "timestamp": int(time.time())}
    save_message(msg.user_id, msg.message, data["timestamp"])
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
