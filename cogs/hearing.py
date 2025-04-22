import discord
from discord.ext import commands, tasks
from discord.utils import get
from helpers.google_logger import (
    log_case_creation,
    append_transcript,
    create_google_doc,
    get_google_doc_link,
    get_google_sheet_link,
    log_case_closure,
)
import datetime
import asyncio

class Hearing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_task.start()
        self.hearing_channels = {}

    def cog_unload(self):
        self.cleanup_task.cancel()

    @commands.command(name="createcase")
    async def create_case(self, ctx, case_id: str, *, reason: str):
        """Creates a new case log entry in Google Sheets."""
        user = ctx.author
        await log_case_creation(case_id, user.name, reason)
        await ctx.send(f"Case `{case_id}` created and logged.")

    @commands.command(name="starthearing")
    async def start_hearing(self, ctx, case_id: str):
        """Creates a temporary hearing text channel for the case."""
        guild = ctx.guild
        category = get(guild.categories, name="Hearings")
        if not category:
            category = await guild.create_category("Hearings")

        channel = await guild.create_text_channel(f"hearing-{case_id}", category=category)
        self.hearing_channels[channel.id] = {
            "case_id": case_id,
            "last_active": datetime.datetime.utcnow(),
        }
        await ctx.send(f"Hearing for `{case_id}` started in {channel.mention}.")

    @commands.command(name="log")
    async def log_message(self, ctx, case_id: str, *, message: str):
        """Appends a message to the hearing's transcript."""
        await append_transcript(case_id, ctx.author.name, message)
        await ctx.send("Message logged.")

    @commands.command(name="closecase")
    async def close_case(self, ctx, case_id: str):
        """Marks a case as closed in Google Sheets."""
        await log_case_closure(case_id)
        await ctx.send(f"Case `{case_id}` marked as closed.")

    @commands.command(name="transcript")
    async def get_transcript(self, ctx, case_id: str):
        """Returns the link to the Google Doc transcript."""
        link = await get_google_doc_link(case_id)
        await ctx.send(f"Transcript: {link}")

    @commands.command(name="sheet")
    async def get_sheet(self, ctx):
        """Returns the link to the master Google Sheet."""
        link = await get_google_sheet_link()
        await ctx.send(f"Master Sheet: {link}")

    @commands.command(name="manual-log")
    async def manual_log(self, ctx, case_id: str, user: str, *, content: str):
        """Manually logs a message on behalf of a user."""
        await append_transcript(case_id, user, content)
        await ctx.send("Manual log added.")

    @commands.command(name="pingjudge")
    async def ping_judge(self, ctx):
        """Notifies judges in the hearing channel."""
        role = get(ctx.guild.roles, name="Judge")
        if role:
            await ctx.send(f"{role.mention}, attention required!")

    @commands.command(name="setjudge")
    async def set_judge(self, ctx, member: discord.Member):
        """Assigns the Judge role to a member."""
        role = get(ctx.guild.roles, name="Judge")
        if role:
            await member.add_roles(role)
            await ctx.send(f"{member.mention} is now a Judge.")

    @commands.command(name="reopen")
    async def reopen_case(self, ctx, case_id: str):
        """Reopens a previously closed case."""
        await ctx.send(f"Reopening case `{case_id}`...")
        # Future: Update Google Sheet or tag reopened state

    @commands.command(name="deletehearing")
    async def delete_hearing(self, ctx, channel: discord.TextChannel):
        """Deletes a hearing channel manually."""
        await channel.delete()
        self.hearing_channels.pop(channel.id, None)

    @commands.command(name="extend")
    async def extend_hearing(self, ctx, channel: discord.TextChannel):
        """Extends the expiration time of a hearing channel."""
        if channel.id in self.hearing_channels:
            self.hearing_channels[channel.id]["last_active"] = datetime.datetime.utcnow()
            await ctx.send(f"Extended {channel.mention}'s lifespan.")

    @commands.command(name="rename")
    async def rename_hearing(self, ctx, new_name: str):
        """Renames the current hearing channel."""
        await ctx.channel.edit(name=new_name)
        await ctx.send(f"Renamed channel to `{new_name}`.")

    @commands.command(name="setcase")
    async def set_case_id(self, ctx, new_case_id: str):
        """Associates the current hearing channel with a new case ID."""
        if ctx.channel.id in self.hearing_channels:
            self.hearing_channels[ctx.channel.id]["case_id"] = new_case_id
            await ctx.send(f"Channel now linked to case `{new_case_id}`.")

    @tasks.loop(minutes=5)
    async def cleanup_task(self):
        """Automatically closes inactive hearing channels after 24 hours."""
        now = datetime.datetime.utcnow()
        for channel_id, info in list(self.hearing_channels.items()):
            if (now - info["last_active"]).total_seconds() > 86400:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.delete()
                self.hearing_channels.pop(channel_id, None)

    @cleanup_task.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Hearing(bot))
