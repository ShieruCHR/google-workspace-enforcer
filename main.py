import asyncio
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
import uvicorn
from api.api_v1 import router as router_v1
from shared import bot
import database

load_dotenv()

app = FastAPI()


def get_bot():
    yield bot


@app.on_event("startup")
async def startup():
    database.create_db()
    app.include_router(router_v1, dependencies=[Depends(get_bot)])
    asyncio.create_task(bot.start(os.getenv("TOKEN")))


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
