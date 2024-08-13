import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
import discord
from discord.ext import commands

if os.path.isfile(".env"):
    from dotenv import load_dotenv

    load_dotenv()

discord.utils.setup_logging()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot("wordware#", intents=intents)


@bot.command("sync")
async def sync(ctx: commands.Context):
    await bot.tree.sync()
    await ctx.message.delete()


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(bot.start(os.getenv("discord")))
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def index():
    return {"detail": "ok"}


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.ware")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=10000)
