import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "reaction_roles.json"

# Load existing reaction role data
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save reaction role data
def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reaction_roles = load_config()

    @commands.command(name="reactionrole_setup")
    @commands.has_permissions(administrator=True)
    async def reactionrole_setup(self, ctx):
        await ctx.send("Please mention the channel containing the message you'd like to use for reaction roles.")

        def check_channel(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.channel_mentions) > 0

        try:
            msg = await self.bot.wait_for('message', check=check_channel, timeout=60.0)
            channel = msg.channel_mentions[0]
        except:
            return await ctx.send("⏰ Timed out or invalid channel.")

        await ctx.send("Please provide the **message ID** of the target message in that channel.")

        def check_id(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check_id, timeout=60.0)
            message_id = int(msg.content.strip())
        except:
            return await ctx.send("⏰ Timed out or invalid message ID.")

        await ctx.send("Please react with the emoji you want to assign a role for.")

        def check_react(reaction, user):
            return user == ctx.author and reaction.message.channel == ctx.channel

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=check_react, timeout=60.0)
            emoji = str(reaction.emoji)
        except:
            return await ctx.send("⏰ Timed out or failed to detect emoji.")

        await ctx.send("Now mention the role you want assigned when users react with that emoji.")

        def check_role(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.role_mentions) > 0

        try:
            msg = await self.bot.wait_for('message', check=check_role, timeout=60.0)
            role = msg.role_mentions[0]
        except:
            return await ctx.send("⏰ Timed out or invalid role.")

        # Save configuration
        key = f"{channel.id}-{message_id}"
        if key not in self.reaction_roles:
            self.reaction_roles[key] = {}

        self.reaction_roles[key][emoji] = role.id
        save_config(self.reaction_roles)

        await ctx.send(f"✅ Reaction role set: reacting with {emoji} gives {role.mention}.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        key = f"{payload.channel_id}-{payload.message_id}"
        emoji = str(payload.emoji)

        if key in self.reaction_roles and emoji in self.reaction_roles[key]:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(self.reaction_roles[key][emoji])
            if role:
                member = guild.get_member(payload.user_id)
                if member:
                    await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        key = f"{payload.channel_id}-{payload.message_id}"
        emoji = str(payload.emoji)

        if key in self.reaction_roles and emoji in self.reaction_roles[key]:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(self.reaction_roles[key][emoji])
            if role:
                member = guild.get_member(payload.user_id)
                if member:
                    await member.remove_roles(role)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
