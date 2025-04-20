import os
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Load cogs
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    # Load the setup cog
    bot.load_extension("cogs.setup")

# Define the main async function to run the bot
async def main():
    await bot.start(os.getenv("DISCORD_TOKEN"))

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
