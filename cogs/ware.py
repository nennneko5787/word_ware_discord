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
        self.setup_generative_ai()
        self.cooldown = []

    def setup_generative_ai(self):
        """Sets up the Google Generative AI model with safety settings."""
        genai.configure(api_key=os.getenv("gemini1"))
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        self.model = genai.GenerativeModel(
            "gemini-1.5-pro-exp-0801", safety_settings=safety_settings
        )

    def is_on_cooldown(self, user: discord.Member) -> bool:
        """Checks if a user is currently on cooldown."""
        return user in self.cooldown

    def start_cooldown(self, user: discord.Member):
        """Adds a user to the cooldown list."""
        self.cooldown.append(user)

    def end_cooldown(self, user: discord.Member):
        """Removes a user from the cooldown list."""
        if user in self.cooldown:
            self.cooldown.remove(user)

    async def fetch_user_messages(
        self, channel: discord.TextChannel, user: discord.Member, limit: int = 50
    ) -> list[discord.Message]:
        """Fetches the latest messages from a user in a given channel."""
        messages = []
        before = datetime.now()
        while len(messages) < limit:
            async for message in channel.history(limit=200, before=before):
                if (
                    not message.content.startswith("wordware#wordware")
                    and message.author.id == user.id
                ):
                    messages.insert(0, message)
            if messages:
                before = messages[0].created_at
        return messages

    def format_messages(self, messages: list[discord.Message]) -> str:
        """Formats messages into a string for AI processing."""
        return (
            "「"
            + "」「".join(
                [
                    f"{message.content}\n> (replyed to {message.reference.resolved.author.display_name if message.reference else 'None'} (@{message.reference.resolved.author.name if message.reference else 'None'})) {message.reference.resolved.content if message.reference else 'None'}"
                    for message in messages
                ]
            )
            + "」"
        )

    @commands.hybrid_command(name="wordware", description="最新50件のメッセージから")
    async def wordware(self, ctx: commands.Context, user: discord.Member):
        if self.is_on_cooldown(ctx.author):
            await ctx.reply("クールダウン中")
            return

        self.start_cooldown(ctx.author)
        await ctx.defer()

        # Randomly select an API key for load balancing
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

        # Fetch and format user messages
        messages = await self.fetch_user_messages(ctx.channel, user)
        if not messages:
            await ctx.reply("指定されたユーザーのメッセージが見つかりませんでした。")
            self.end_cooldown(ctx.author)
            return

        formatted_messages = self.format_messages(messages)

        # Generate content using the AI model
        prompt = f"""
            {user.display_name} (@{user.name}) の悪いところを文章にしてください。ユーザー名やユーザーIDにも触れてください。
            このユーザーのメッセージ一覧は以下のとおりです。
            {formatted_messages}
        """
        response = await asyncio.to_thread(self.model.generate_content, prompt)

        # Reply with the generated content
        await ctx.reply(response.text)
        self.end_cooldown(ctx.author)


async def setup(bot: commands.Bot):
    await bot.add_cog(WordWareCog(bot))
