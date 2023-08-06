import asyncio
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
import uvicorn
from api.api_v1 import router as router_v1
from shared import bot

load_dotenv()

app = FastAPI()


def get_bot():
    yield bot


@app.on_event("startup")
async def startup():
    app.include_router(router_v1, dependencies=[Depends(get_bot)])
    if bool(int(os.getenv("PUBLIC_BOT_FEATURES", "0"))):
        print("Loading extension for public bot...")
        await bot.load_extension("cogs.public_bot")
    asyncio.create_task(bot.start(os.getenv("TOKEN")))


async def custom_exception_handler(request, exc):
    status_code = exc.status_code if isinstance(exc, HTTPException) else 500
    return FileResponse("failed.html", status_code=status_code)


# FastAPIアプリケーションにException Middlewareを追加
app.add_exception_handler(Exception, custom_exception_handler)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
