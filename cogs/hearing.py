import discord
from discord.ext import commands, tasks
import datetime

class Hearing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_activity = {}  # To track last activity in channels
        self.clean_inactive_hearings.start()  # Start the loop

    @tasks.loop(minutes=60)
    async def clean_inactive_hearings(self):
        current_time = datetime.datetime.utcnow()
        threshold = datetime.timedelta(hours=24)  # Channels inactive for 24 hours will be deleted

        for channel_id, last_activity_time in list(self.last_activity.items()):
            if current_time - last_activity_time > threshold:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await channel.delete()  # Delete inactive channels
                    self.last_activity.pop(channel_id)  # Remove from tracking list

    @clean_inactive_hearings.before_loop
    async def before_clean_inactive_hearings(self):
        await self.bot.wait_until_ready()
        print("Cleaning inactive hearings...")  

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def hearing_reopen(self, ctx, channel_name: str, *members: discord.Member):
        guild = ctx.guild
        category_name = "Court Hearings"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            await ctx.send("\u274c Hearing category not found.")
            return

        if discord.utils.get(category.text_channels, name=channel_name):
            await ctx.send("\u274c That channel already exists.")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True)
        }

        for member in members:
            overwrites[member] = discord.Permission
