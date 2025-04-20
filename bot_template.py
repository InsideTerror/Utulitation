import discord
from discord.ext import commands

# Set up the bot with a command prefix, e.g., "!":
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Template data for roles and channels
TEMPLATE = {
    "roles": [
        {"name": "SC", "color": discord.Color.gold()},
        {"name": "Military", "color": discord.Color.green()},
        {"name": "Police", "color": discord.Color.blue()},
        {"name": "CATS", "color": discord.Color.purple()},
        {"name": "Civilians", "color": discord.Color.light_grey()},
        {"name": "Admin", "color": discord.Color.red()},
        {"name": "Bot", "color": discord.Color.teal()},
        {"name": "Muted", "color": discord.Color.dark_grey()}
    ],
    "categories": [
        {"name": "📢 Information", "channels": ["server-announcements", "rules", "role-assignment"]},
        {"name": "💬 General", "channels": ["general-chat", "introductions", "support"]},
        {"name": "🏛️ SC Headquarters", "channels": ["sc-council-room", "sc-voting", "sc-archives"]},
        {"name": "🎖 Military Zone", "channels": ["military-ops", "military-strategy", "military-radio"]},
        {"name": "👮 Police Station", "channels": ["law-enforcement", "case-reports", "radio-channel"]},
        {"name": "🕵️ CATS Division", "channels": ["intelligence-briefings", "investigation-board", "comms-hub"]},
        {"name": "🗣 Civilian Area", "channels": ["civilian-lounge", "suggestions", "public-discussions"]},
        {"name": "🤖 Bot Zone", "channels": ["commands", "logs"]}
    ]
}

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_server(ctx):
    guild = ctx.guild

    # Create roles
    for role_data in TEMPLATE["roles"]:
        await guild.create_role(name=role_data["name"], color=role_data["color"])

    await ctx.send("✅ Roles created.")

    # Create categories and channels
    for category_data in TEMPLATE["categories"]:
        category = await guild.create_category(category_data["name"])
        for channel_name in category_data["channels"]:
            if "radio" in channel_name or "comms" in channel_name:
                await guild.create_voice_channel(channel_name, category=category)
            else:
                await guild.create_text_channel(channel_name, category=category)

    await ctx.send("✅ Server structure created.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def hearing_create(ctx, *members: discord.Member):
    guild = ctx.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }

    # Allow all mentioned users
    for member in members:
        overwrites[member] = discord.PermissionOverwrite(read_messages=True)

    # Optional: Allow a specific role like "Judge" or "Admin" access
    judge_role = discord.utils.get(guild.roles, name="SC")  # Change to your judge role if different
    if judge_role:
        overwrites[judge_role] = discord.PermissionOverwrite(read_messages=True)

    # Find next available hearing channel number
    existing = [c for c in guild.text_channels if c.name.startswith("hearing-")]
    next_number = len(existing) + 1
    channel_name = f"hearing-{next_number}"

    # Create the private channel
    channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=None)
    
    await ctx.send(f"✅ Hearing channel `{channel.mention}` created and access granted to specified users.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def hearing_close(ctx):
    if ctx.channel.name.startswith("hearing-"):
        await ctx.send("🔒 Closing this hearing channel...")
        await ctx.channel.delete()
    else:
        await ctx.send("❌ This command can only be used inside a hearing channel.")


# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot.run("put your token here")
