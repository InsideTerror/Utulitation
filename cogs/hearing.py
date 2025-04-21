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
    # Ensure the command can be run in any channel
    if ctx.channel.name == "commands":  # Adjust if needed for your server setup
        if ctx.channel.name.startswith("hearing-"):
            await ctx.send("\ud83d\udd10 Closing this hearing channel...")
            await ctx.channel.delete()
            self.last_activity.pop(ctx.channel.id, None)
        else:
            await ctx.send("\u274c This command can only be used inside a hearing channel or the #commands channel.")
    else:
        await ctx.send("This command can only be used in the #commands channel or a hearing.")

@commands.command()
@commands.has_permissions(manage_channels=True)
async def hearing_reopen(self, ctx, channel_name: str, *members: discord.Member):
    guild = ctx.guild
    category_name = "Court Hearings"
    category = discord.utils.get(guild.categories, name=category_name)
    if not category:
        await ctx.send("\u274c Hearing category not found.")
        return

    # Check if the hearing channel exists, and reopen it
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if channel:
        if channel.name.startswith("hearing-"):
            # Reopen the hearing channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True)
            }

            for member in members:
                overwrites[member] = discord.PermissionOverwrite(read_messages=True)

            judge_role = discord.utils.get(guild.roles, name="SC")
            if judge_role:
                overwrites[judge_role] = discord.PermissionOverwrite(read_messages=True)

            await channel.edit(overwrites=overwrites)
            await ctx.send(f"\ud83d\udd01 Reopened the hearing channel `{channel_name}`.")
        else:
            await ctx.send(f"\u274c The channel `{channel_name}` is not a hearing channel.")
    else:
        await ctx.send("\u274c That channel does not exist.")


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
import discord
from discord.ext import commands
import asyncio

@commands.command()
async def hearing_end(ctx, channel_name):
    # Get the channel by name
    channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
    
    if not channel:
        await ctx.send("Channel not found.")
        return

    # Check if the channel has had any messages in the last 24 hours
    last_message_time = channel.last_message.created_at if channel.last_message else channel.created_at

    if (discord.utils.utcnow() - last_message_time).total_seconds() > 86400:  # 24 hours
        await channel.delete()
        await ctx.send(f"Channel {channel_name} has been deleted due to inactivity.")
    else:
        await ctx.send(f"Channel {channel_name} is still active.")

@commands.command(name="hearing_force_end")
@commands.has_permissions(manage_channels=True)
async def hearing_force_end(self, ctx):
    """Force deletes the current hearing channel immediately."""
    channel = ctx.channel
    if channel.name.startswith("hearing-"):
        await channel.delete()
        await ctx.send("🔒 Hearing channel has been force-closed.", delete_after=5)
    else:
        await ctx.send("This command must be used in a hearing channel.")
@commands.command(name="delete_hearing")
@commands.has_permissions(manage_channels=True)
async def delete_hearing(self, ctx, channel_name: str):
    """Deletes a specific hearing channel by name."""
    guild = ctx.guild
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    
    if channel and channel.name.startswith("hearing-"):
        await channel.delete()
        await ctx.send(f"🔒 {channel_name} has been deleted.", delete_after=5)
    else:
        await ctx.send(f"No hearing channel found with the name `{channel_name}`.", delete_after=5)


async def setup(bot):
    await bot.add_cog(Hearing(bot))
