import discord
from discord.ext import commands
from discord.utils import get
import asyncio
import datetime

HEARING_CATEGORY_NAME = "Hearings"
AUTHORIZED_ROLES = ["SC", "Judge"]
INACTIVITY_TIMEOUT = 86400  # 24 hours
LOG_CHANNEL_NAME = "case-directory"

class Hearing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_timers = {}

    async def get_log_channel(self, guild):
        return get(guild.text_channels, name=LOG_CHANNEL_NAME)

    async def log_action(self, guild, title, description, color=discord.Color.green()):
        log_channel = await self.get_log_channel(guild)
        if log_channel:
            embed = discord.Embed(title=title, description=description, color=color)
            embed.timestamp = datetime.datetime.utcnow()
            await log_channel.send(embed=embed)

    async def close_channel_after_timeout(self, channel: discord.TextChannel):
        await asyncio.sleep(INACTIVITY_TIMEOUT)
        if channel.id in self.channel_timers:
            try:
                await channel.set_permissions(channel.guild.default_role, overwrite=discord.PermissionOverwrite(read_messages=False))
                await channel.send("🔒 This hearing channel has been closed due to 24 hours of inactivity.")
                await self.log_action(channel.guild, "Hearing Auto-Closed",
                    f"{channel.mention} was closed automatically due to inactivity.")
                del self.channel_timers[channel.id]
            except Exception as e:
                print(f"Failed to close channel {channel.name}: {e}")

    def has_authorized_role(self, member):
        return any(role.name in AUTHORIZED_ROLES for role in member.roles)

    @commands.command(name="hearing")
    async def create_hearing(self, ctx, *, reason="No reason provided"):
        guild = ctx.guild
        category = get(guild.categories, name=HEARING_CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(HEARING_CATEGORY_NAME)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        for role_name in AUTHORIZED_ROLES:
            role = get(guild.roles, name=role_name)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel_name = f"hearing-{ctx.author.name.lower()}-{ctx.author.discriminator}"
        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        await channel.send(f"{ctx.author.mention} created this hearing for: **{reason}**")

        self.channel_timers[channel.id] = datetime.datetime.utcnow()
        self.bot.loop.create_task(self.close_channel_after_timeout(channel))

        await self.log_action(guild, "Hearing Created",
            f"Channel: {channel.mention}\nCreated by: {ctx.author.mention}\nReason: {reason}")

        await ctx.send(f"Hearing channel created: {channel.mention}")

    @commands.command(name="reopen_hearing")
    async def reopen_hearing(self, ctx, channel: discord.TextChannel):
        if not self.has_authorized_role(ctx.author):
            return await ctx.send("❌ You don't have permission to reopen hearings.")

        await channel.set_permissions(channel.guild.default_role, overwrite=discord.PermissionOverwrite(read_messages=False))
        for role_name in AUTHORIZED_ROLES:
            role = get(channel.guild.roles, name=role_name)
            if role:
                await channel.set_permissions(role, read_messages=True, send_messages=True)

        await channel.send("🔓 This hearing has been reopened by an authorized member.")
        self.channel_timers[channel.id] = datetime.datetime.utcnow()
        self.bot.loop.create_task(self.close_channel_after_timeout(channel))

        await self.log_action(ctx.guild, "Hearing Reopened",
            f"{channel.mention} was reopened by {ctx.author.mention}.")

        await ctx.send(f"{channel.mention} has been reopened.")

    @commands.command(name="end_hearing")
    async def end_hearing(self, ctx, channel: discord.TextChannel):
        if not self.has_authorized_role(ctx.author):
            return await ctx.send("❌ You don't have permission to end hearings.")

        await channel.set_permissions(channel.guild.default_role, overwrite=discord.PermissionOverwrite(read_messages=False))
        await channel.send("🛑 This hearing has been forcefully ended by an authorized user.")
        if channel.id in self.channel_timers:
            del self.channel_timers[channel.id]

        await self.log_action(ctx.guild, "Hearing Ended",
            f"{channel.mention} was ended by {ctx.author.mention}.")

        await ctx.send(f"{channel.mention} has been closed.")

    @commands.command(name="hearing_help")
    async def hearing_help(self, ctx):
        embed = discord.Embed(
            title="🎙️ Hearing System – Commands Menu",
            color=discord.Color.blue(),
            description="Manage court hearings with temporary private channels."
        )
        embed.add_field(name="📥 `!hearing [reason]`", value="Create a new hearing channel.", inline=False)
        embed.add_field(name="🔓 `!reopen_hearing #channel`", value="Reopen a closed hearing (SC or Judge only).", inline=False)
        embed.add_field(name="🛑 `!end_hearing #channel`", value="Force-end a hearing channel (SC or Judge only).", inline=False)
        embed.add_field(name="📘 `!hearing_help`", value="Show this help menu.", inline=False)
        embed.set_footer(text="CATS Judicial Tools – Cloudville")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Hearing(bot))
