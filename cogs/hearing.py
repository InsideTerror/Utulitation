import discord
from discord.ext import commands, tasks
from discord.utils import get
from datetime import datetime, timedelta
import asyncio

from .helpers.google_logger import log_case_creation, append_transcript

CATEGORY_NAME = "Hearings"
CASE_LOG_CHANNEL = "case-directory"
HEARING_INACTIVITY_LIMIT = 60 * 60 * 24  # 24 hours


class Hearing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_inactive_channels.start()

    def cog_unload(self):
        self.cleanup_inactive_channels.cancel()

    @commands.command(name="starthearing")
    async def start_hearing(self, ctx, case_id: str):
        """Starts a new hearing and creates a temporary channel."""
        guild = ctx.guild
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        if not category:
            category = await guild.create_category(CATEGORY_NAME)

        channel_name = f"hearing-{case_id}"
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await ctx.send(f"A hearing for case `{case_id}` already exists: {existing_channel.mention}")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        timestamp = datetime.utcnow().isoformat()
        log_channel = discord.utils.get(guild.text_channels, name=CASE_LOG_CHANNEL)

        if log_channel:
            await log_channel.send(f"📂 Hearing `{case_id}` created by {ctx.author.mention} at `{timestamp}`")

        await log_case_creation(case_id, ctx.author.name, timestamp)

        await ctx.send(f"Hearing for case `{case_id}` started in {channel.mention}")

    @commands.command(name="endhearing")
    async def end_hearing(self, ctx, case_id: str):
        """Ends a hearing and deletes the corresponding channel."""
        channel_name = f"hearing-{case_id}"
        channel = discord.utils.get(ctx.guild.channels, name=channel_name)

        if not channel:
            await ctx.send(f"No active hearing found for case `{case_id}`.")
            return

        await channel.delete()
        await ctx.send(f"Hearing for case `{case_id}` has been ended and the channel was removed.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        if message.channel.name.startswith("hearing-"):
            case_id = message.channel.name.replace("hearing-", "")
            await append_transcript(case_id, message.author.name, message.content, message.created_at)

    @tasks.loop(minutes=10)
    async def cleanup_inactive_channels(self):
        now = datetime.utcnow()
        for guild in self.bot.guilds:
            category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
            if not category:
                continue

            for channel in category.text_channels:
                history = [msg async for msg in channel.history(limit=1)]
                if not history:
                    continue

                last_message_time = history[0].created_at
                if (now - last_message_time).total_seconds() > HEARING_INACTIVITY_LIMIT:
                    await channel.delete()


async def setup(bot):
    await bot.add_cog(Hearing(bot))
