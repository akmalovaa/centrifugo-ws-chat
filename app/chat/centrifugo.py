import time

import aiohttp
import jwt

from chat.settings import settings


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
