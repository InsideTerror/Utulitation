import discord
from discord.ext import commands, tasks
import datetime

class Hearing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_activity = {}
        self.clean_inactive_hearings.start()

    def cog_unload(self):
        self.clean_inactive_hearings.cancel()

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def hearing_create(self, ctx, *members: discord.Member):
        guild = ctx.guild
        category_name = "Court Hearings"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True)
        }

        for member in members:
            overwrites[member] = discord.PermissionOverwrite(read_messages=True)

        judge_role = discord.utils.get(guild.roles, name="SC")
        if judge_role:
            overwrites[judge_role] = discord.PermissionOverwrite(read_messages=True)

        existing_channels = [c for c in category.text_channels if c.name.startswith("hearing-")]
        next_number = len(existing_channels) + 1
        channel_name = f"hearing-{next_number}"

        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        self.last_activity[channel.id] = datetime.datetime.utcnow()

        await ctx.send(f"\u2705 Hearing channel `{channel.mention}` created.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def hearing_close(self, ctx):
        if ctx.channel.name.startswith("hearing-"):
            await ctx.send("\ud83d\udd10 Closing this hearing channel...")
            await ctx.channel.delete()
            self.last_activity.pop(ctx.channel.id, None)
        else:
            await ctx.send("\u274c This command can only be used inside a hearing channel.")

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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.name.startswith("hearing-") and not message.author.bot:
            self.last_activity[message.channel.id] = datetime.datetime.utcnow()

    @tasks.loop(minutes=60)
    async def clean_inactive_hearings(self):
        now = datetime.datetime.utcnow()
        to_delete = []

        for channel_id, last_time in self.last_activity.items():
            delta = now - last_time
            if delta.total_seconds() > 86400:  # 24 hours
                to_delete.append(channel_id)

        for channel_id in to_delete:
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send("\u23f0 Channel inactive for 24 hours. Closing hearing.")
                    await channel.delete()
                except:
                    pass
            self.last_activity.pop(channel_id, None)

async def setup(bot):
    await bot.add_cog(Hearing(bot))
