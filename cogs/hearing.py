import discord
from discord.ext import commands
from datetime import datetime
from helpers.google_logger import log_case_creation, append_transcript  # Corrected import

class Hearing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="start_hearing")
    async def start_hearing(self, ctx, case_id: str, *parties: str):
        """Starts a new hearing and logs it."""
        # Prepare the case details
        case_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        case_parties = ', '.join(parties)
        
        # Log to Google Sheets
        log_case_creation(case_id, case_date, case_parties)
        
        # Create a hearing channel in Discord
        category = discord.utils.get(ctx.guild.categories, name="Hearings")
        hearing_channel = await ctx.guild.create_text_channel(
            f"hearing-{case_id}", category=category
        )
        
        # Send a confirmation message
        await ctx.send(f"Hearing for case {case_id} started successfully! Channel: {hearing_channel.mention}")
    
    @commands.command(name="end_hearing")
    async def end_hearing(self, ctx, case_id: str):
        """Ends a hearing and updates the case status."""
        # Fetch the hearing channel
        hearing_channel = discord.utils.get(ctx.guild.text_channels, name=f"hearing-{case_id}")
        
        if hearing_channel:
            # Delete the hearing channel
            await hearing_channel.delete()
            await ctx.send(f"Hearing for case {case_id} has ended and the channel has been deleted.")
        else:
            await ctx.send(f"Hearing for case {case_id} not found.")
    
    @commands.command(name="log_transcript")
    async def log_transcript(self, ctx, case_id: str, *, message: str):
        """Logs a transcript message for a case."""
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Append the message to the Google Doc for this case
        append_transcript(case_id, timestamp, message)
        
        # Log in Discord
        await ctx.send(f"Transcript for case {case_id} logged: {message}")

    @commands.command(name="list_hearings")
    async def list_hearings(self, ctx):
        """Lists all active hearings."""
        hearings = [channel.name for channel in ctx.guild.text_channels if channel.name.startswith("hearing-")]
        if hearings:
            await ctx.send(f"Active hearings: {', '.join(hearings)}")
        else:
            await ctx.send("No active hearings found.")

def setup(bot):
    bot.add_cog(Hearing(bot))
