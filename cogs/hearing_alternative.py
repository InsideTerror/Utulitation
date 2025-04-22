"""
Hearing-related cog for Discord bot with logging to Google Sheets and Docs.
Commands use prefix (!) and handle court-like procedures, logs everything via google_logger.
Railway-compatible with env var-based Google credentials.
"""

import discord
from discord.ext import commands, tasks
from discord.utils import get
from datetime import datetime, timedelta
import asyncio
import os

from helpers.google_logger import (
    log_case_creation,
    log_case_closure,
    log_participant,
    log_message,
    append_transcript,
    reopen_case,
)

class Hearing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.inactive_check.start()
        self.active_hearings = {}  # {channel_id: last_active_time}

    @commands.command()
    async def create_hearing(self, ctx, case_id: str, *, title: str):
        category = get(ctx.guild.categories, name="Hearings")
        if not category:
            category = await ctx.guild.create_category("Hearings")

        channel = await ctx.guild.create_text_channel(name=f"hearing-{case_id}", category=category)
        await channel.set_permissions(ctx.guild.default_role, read_messages=False)
        await channel.set_permissions(ctx.author, read_messages=True, send_messages=True)

        now = datetime.utcnow()
        self.active_hearings[channel.id] = now

        await log_case_creation(case_id, ctx.author.name, title, now)
        await channel.send(f"Case `{case_id}` started by {ctx.author.mention}.")

    @commands.command()
    async def close_hearing(self, ctx, case_id: str):
        channel = ctx.channel
        await log_case_closure(case_id, datetime.utcnow())
        await channel.send("This hearing is now closed.")
        await channel.edit(name=f"closed-{case_id}")
        self.active_hearings.pop(channel.id, None)

    @commands.command()
    async def reopen_hearing(self, ctx, case_id: str):
        channel = ctx.channel
        await reopen_case(case_id)
        await channel.send("Hearing reopened.")
        self.active_hearings[channel.id] = datetime.utcnow()

    @commands.command()
    async def join_hearing(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, read_messages=True, send_messages=True)
        await log_participant(ctx.channel.name, member.name, "joined")
        await ctx.send(f"{member.mention} added to hearing.")

    @commands.command()
    async def leave_hearing(self, ctx, member: discord.Member):
        await ctx.channel.set_permissions(member, overwrite=None)
        await log_participant(ctx.channel.name, member.name, "left")
        await ctx.send(f"{member.mention} removed from hearing.")

    @commands.command()
    async def log_message(self, ctx, *, message: str):
        await log_message(ctx.channel.name, ctx.author.name, message, datetime.utcnow())
        await ctx.send("Message logged.")

    @commands.command()
    async def transcript(self, ctx, *, message: str):
        await append_transcript(ctx.channel.name, ctx.author.name, message)
        await ctx.send("Transcript updated.")

    @commands.command()
    async def list_hearings(self, ctx):
        hearings = [c.name for c in ctx.guild.text_channels if c.category and c.category.name == "Hearings"]
        await ctx.send("Open Hearings:\n" + "\n".join(hearings))

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Hearing bot is operational.")

    @commands.command()
    async def update_title(self, ctx, case_id: str, *, new_title: str):
        await log_case_creation(case_id, ctx.author.name, new_title, datetime.utcnow())
        await ctx.send(f"Title updated for case {case_id}.")

    @commands.command()
    async def rename_hearing(self, ctx, *, new_name: str):
        await ctx.channel.edit(name=new_name)
        await ctx.send("Channel renamed.")

    @commands.command()
    async def remove_hearing(self, ctx):
        await ctx.send("Deleting this channel.")
        await ctx.channel.delete()

    @commands.command()
    async def extend_timer(self, ctx):
        self.active_hearings[ctx.channel.id] = datetime.utcnow()
        await ctx.send("Timer extended.")

    @commands.command()
    async def help_hearing(self, ctx):
        await ctx.send("""Available Hearing Commands:
!create_hearing <case_id> <title>
!close_hearing <case_id>
!reopen_hearing <case_id>
!join_hearing @user
!leave_hearing @user
!log_message <text>
!transcript <text>
!list_hearings
!ping
!update_title <case_id> <new title>
!rename_hearing <new_name>
!remove_hearing
!extend_timer
!help_hearing
""")

    @tasks.loop(minutes=5)
    async def inactive_check(self):
        now = datetime.utcnow()
        to_close = []
        for channel_id, last_time in self.active_hearings.items():
            if now - last_time > timedelta(hours=24):
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.send("Auto-closing due to inactivity.")
                    await channel.edit(name=f"closed-{channel.name}")
                    to_close.append(channel_id)
        for cid in to_close:
            self.active_hearings.pop(cid, None)

async def setup(bot):
    await bot.add_cog(Hearing(bot))
