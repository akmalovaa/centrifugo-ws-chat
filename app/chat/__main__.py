import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from chat.db import init_db
from chat.routes import setup_routes
from chat.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
setup_routes(app)

if __name__ == "__main__":
    log_format = "%(levelname)s:     %(message)s"
    logging.basicConfig(
        level=settings.log_level,
        format=log_format,
    )
    logging.info("APP start ✅, listening on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
