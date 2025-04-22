import discord
from discord.ext import commands
from helpers.google_logger import log_case_creation, append_transcript
import asyncio

class Hearing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hearing_channels = {}

    # Command to create a new case
    @commands.command()
    async def create_case(self, ctx, case_name: str, *, case_details: str):
        """Create a new case and log it"""
        log_case_creation(case_name, case_details)
        await ctx.send(f"Case '{case_name}' has been created and logged.")

    # Command to append a message to an existing case transcript
    @commands.command()
    async def append_message(self, ctx, case_id: str, *, message: str):
        """Append a message to a case transcript"""
        append_transcript(case_id, message)
        await ctx.send(f"Message appended to case {case_id}.")

    # Command to start a hearing and create a text channel
    @commands.command()
    async def start_hearing(self, ctx, case_id: str):
        """Start a hearing for a specific case"""
        channel = await ctx.guild.create_text_channel(f"hearing-{case_id}")
        self.hearing_channels[case_id] = channel.id
        await ctx.send(f"Hearing channel for case {case_id} created: {channel.mention}")

    # Command to end the hearing and delete the text channel
    @commands.command()
    async def end_hearing(self, ctx, case_id: str):
        """End a hearing and delete its channel"""
        channel_id = self.hearing_channels.get(case_id)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            await channel.delete()
            del self.hearing_channels[case_id]
            await ctx.send(f"Hearing for case {case_id} ended and channel deleted.")
        else:
            await ctx.send(f"No hearing found for case {case_id}.")

    # Command to reopen a hearing channel
    @commands.command()
    async def reopen_hearing(self, ctx, case_id: str):
        """Reopen a hearing channel"""
        if case_id in self.hearing_channels:
            await ctx.send(f"Hearing for case {case_id} is already active.")
        else:
            channel = await ctx.guild.create_text_channel(f"hearing-{case_id}")
            self.hearing_channels[case_id] = channel.id
            await ctx.send(f"Hearing channel for case {case_id} reopened: {channel.mention}")

    # Command to log case information
    @commands.command()
    async def log_case_info(self, ctx, case_id: str):
        """Retrieve and log case information"""
        case_info = f"Info for case {case_id}"
        await ctx.send(f"Case information for {case_id}: {case_info}")
        append_transcript(case_id, case_info)

    # Command to log the current hearing transcript
    @commands.command()
    async def log_transcript(self, ctx, case_id: str):
        """Log current transcript from a hearing"""
        case_transcript = f"Transcript for case {case_id}"
        append_transcript(case_id, case_transcript)
        await ctx.send(f"Transcript for case {case_id} logged.")

    # Command to list all open hearings
    @commands.command()
    async def list_hearings(self, ctx):
        """List all currently open hearings"""
        if self.hearing_channels:
            hearings = "\n".join([f"Case {case_id}: <#{channel_id}>" for case_id, channel_id in self.hearing_channels.items()])
            await ctx.send(f"Open hearings:\n{hearings}")
        else:
            await ctx.send("No hearings are currently open.")

    # Command to get case status (if the hearing is ongoing)
    @commands.command()
    async def get_case_status(self, ctx, case_id: str):
        """Get the current status of a case (whether hearing is ongoing or not)"""
        if case_id in self.hearing_channels:
            await ctx.send(f"Hearing for case {case_id} is currently ongoing.")
        else:
            await ctx.send(f"No hearing found for case {case_id}.")

    # Command to view case transcript
    @commands.command()
    async def view_case_transcript(self, ctx, case_id: str):
        """View the transcript of a case"""
        await ctx.send(f"Here is the transcript for case {case_id}:")
        append_transcript(case_id, "Viewing transcript.")

    # Command to clear a case's transcript
    @commands.command()
    async def clear_transcript(self, ctx, case_id: str):
        """Clear the transcript of a case"""
        await ctx.send(f"Transcript for case {case_id} has been cleared.")
        # You would implement the actual clearing process if needed.

    # Command to set a case as closed
    @commands.command()
    async def close_case(self, ctx, case_id: str):
        """Close a case"""
        if case_id in self.hearing_channels:
            await self.end_hearing(ctx, case_id)
        else:
            await ctx.send(f"Case {case_id} has already been closed.")

    # Command to reopen a closed case (if needed)
    @commands.command()
    async def reopen_case(self, ctx, case_id: str):
        """Reopen a closed case"""
        await self.reopen_hearing(ctx, case_id)

    # Command to announce hearing details in the server
    @commands.command()
    async def announce_hearing(self, ctx, case_id: str):
        """Announce the details of an ongoing hearing in the server"""
        hearing_channel = self.hearing_channels.get(case_id)
        if hearing_channel:
            channel = self.bot.get_channel(hearing_channel)
            await channel.send(f"Attention: Hearing for case {case_id} is ongoing.")
        else:
            await ctx.send(f"No ongoing hearing found for case {case_id}.")

    # Command to give a case a final verdict
    @commands.command()
    async def verdict(self, ctx, case_id: str, *, verdict_message: str):
        """Give a final verdict on a case"""
        await ctx.send(f"Verdict for case {case_id}: {verdict_message}")
        append_transcript(case_id, f"Verdict: {verdict_message}")

    # Command to fetch the hearing details for a specific case
    @commands.command()
    async def fetch_hearing_details(self, ctx, case_id: str):
        """Fetch the hearing details for a specific case"""
        await ctx.send(f"Hearing details for case {case_id}: <#channel_id>")

async def setup(bot):
    bot.add_cog(Hearing(bot))
