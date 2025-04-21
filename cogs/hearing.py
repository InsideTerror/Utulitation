import discord
from discord.ext import commands, tasks
import datetime

class Hearing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_activity = {}  # To track last activity in channels
        self.clean_inactive_hearings.start()  # Start the loop

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
            overwrites[member] = discord.PermissionOverwrite(read_messages=True)

        judge_role = discord.utils.get(guild.roles, name="SC")
        if judge_role:
            overwrites[judge_role] = discord.PermissionOverwrite(read_messages=True)

        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        self.last_activity[channel.id] = datetime.datetime.utcnow()

        await ctx.send(f"\ud83d\udd01 Reopened channel `{channel.mention}`.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def hearing_close(self, ctx):
        if ctx.channel.name.startswith("hearing-"):
            await ctx.send("\ud83d\udd10 Closing this hearing channel...")
            await ctx.channel.delete()
            self.last_activity.pop(ctx.channel.id, None)
        else:
            await ctx.send("\u274c This command can only be used inside a hearing channel.")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.name.startswith("hearing-") and not message.author.bot:
            self.last_activity[message.channel.id] = datetime.datetime.utcnow()

def setup(bot):
    bot.add_cog(Hearing(bot))
