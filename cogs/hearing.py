import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from helpers.google_logger import GoogleLogger

google_logger = GoogleLogger()

class Hearing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_hearings = {}
        self.check_expiring_hearings.start()  # Start the background task

    @commands.command(name="start_hearing")
    async def start_hearing(self, ctx, case_id: str, judge: str, parties: str):
        """Starts a hearing and logs it to the sheet."""
        timestamp = str(ctx.message.created_at)
        status = "Pending"
        # Log to Google Sheets
        await google_logger.log_case_to_sheet(case_id, judge, parties, status, timestamp)
        # Log case creation in Google Docs
        await google_logger.log_case_creation(case_id, judge, parties, status, timestamp)
        # Track the hearing start time
        self.active_hearings[case_id] = datetime.now()
        await ctx.send(f"Hearing for case {case_id} started by Judge {judge}.")

    @commands.command(name="append_transcript")
    async def append_transcript(self, ctx, case_id: str, content: str):
        """Appends a transcript line."""
        user = ctx.author.name
        timestamp = str(ctx.message.created_at)
        # Append transcript to Google Docs
        await google_logger.append_transcript(case_id, user, content, timestamp)
        await ctx.send(f"Transcript for case {case_id} updated with content: {content}.")

    @commands.command(name="close_hearing")
    async def close_hearing(self, ctx, case_id: str):
        """Closes the hearing and updates the status in the sheet."""
        timestamp = str(ctx.message.created_at)
        status = "Closed"
        # Update status in Google Sheets
        await google_logger.log_case_to_sheet(case_id, ctx.author.name, "N/A", status, timestamp)
        self.active_hearings.pop(case_id, None)
        await ctx.send(f"Hearing for case {case_id} closed by Judge {ctx.author.name}.")

    @tasks.loop(minutes=10)  # This will run every 10 minutes
    async def check_expiring_hearings(self):
        """Checks for hearings that have been inactive for 24 hours and closes them."""
        current_time = datetime.now()
        for case_id, start_time in list(self.active_hearings.items()):
            if current_time - start_time > timedelta(hours=24):
                # Close the hearing automatically if it's been inactive for more than 24 hours
                status = "Expired"
                timestamp = str(current_time)
                await google_logger.log_case_to_sheet(case_id, "System", "N/A", status, timestamp)
                self.active_hearings.pop(case_id, None)
                # You can also send a message or log it elsewhere
                print(f"Hearing for case {case_id} has expired.")

def setup(bot):
    bot.add_cog(Hearing(bot))
