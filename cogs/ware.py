import os
import asyncio
import random
from datetime import datetime

import discord
from discord.ext import commands
import google.generativeai as genai

if os.path.isfile(".env"):
    from dotenv import load_dotenv

    load_dotenv()


class WordWareCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        genai.configure(api_key=os.getenv("gemini1"))
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        self.model: genai.GenerativeModel = genai.GenerativeModel(
            "gemini-1.5-pro-exp-0801", safety_settings=safety
        )
        self.cooldown: list[discord.Member] = []

    @commands.hybrid_command(name="wordware", description="最新50件のメッセージから")
    async def wordware(self, ctx: commands.Context, user: discord.Member):
        if ctx.author in self.cooldown:
            await ctx.reply("クールダウン中")
        self.cooldown.append(ctx.author)
        await ctx.defer()
        genai.configure(
            api_key=random.choice(
                [
                    os.getenv("gemini1"),
                    os.getenv("gemini2"),
                    os.getenv("gemini3"),
                    os.getenv("gemini4"),
                ]
            )
        )
        messages: list[discord.Message] = []
        before = datetime.now()
        while len(messages) < 50:
            async for message in ctx.channel.history(limit=200, before=before):
                if message.author == user:
                    messages.append(message)
            if len(messages) > 0:
                before = messages[-1].created_at
        twiito = "「" + "」「".join([message.content for message in messages]) + "」"

        response = await asyncio.to_thread(
            self.model.generate_content,
            f"""
                {user.display_name} (@{user.name}) の悪いところを文章にしてください。ユーザー名やユーザーIDにも触れてください。
                このユーザーのメッセージ一覧は以下のとおりです。
                {twiito}
            """,
        )
        await ctx.reply(response.text)
        self.cooldown.remove(ctx.author)


async def setup(bot: commands.Bot):
    await bot.add_cog(WordWareCog(bot))
