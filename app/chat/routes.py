import time

from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chat.centrifugo import generate_centrifugo_token, publish_to_centrifugo
from chat.db import get_last_messages, save_message
from chat.manager import ConnectionManager
from chat.models import Message
from chat.settings import settings


manager = ConnectionManager()
templates = Jinja2Templates(directory="templates")


def setup_routes(app) -> None:
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        user_id = "user_" + str(int(time.time()))
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
