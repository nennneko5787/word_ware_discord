import os

import discord
from discord.ext import commands

if os.path.isfile(".env"):
    from dotenv import load_dotenv

    load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot("wordware#", intents=intents)


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.ware")


bot.run(os.getenv("discord"))
