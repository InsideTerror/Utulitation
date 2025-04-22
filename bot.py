import os
import discord
from discord.ext import commands
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure intents for the bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Required for reading message content
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"✅ Logged in as {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for commands."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Please check your command usage.")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send("❌ An error occurred while running this command.")
        logger.error(f"CommandInvokeError: {error}")
    else:
        await ctx.send("❌ An unexpected error occurred.")
        logger.error(f"Unexpected error: {error}")

async def load_extensions():
    """Dynamically load all the cogs/extensions."""
    try:
        # Load all your cogs here
        await bot.load_extension("cogs.setup")
        await bot.load_extension("cogs.hearing")  # If you're using this too
        await bot.load_extension("cogs.reaction_roles")  # Added reaction_roles cog
        logger.info("✅ All extensions loaded successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to load extensions: {e}")

async def main():
    """Main entry point for the bot."""
    async with bot:
        await load_extensions()
        try:
            await bot.start(os.getenv("DISCORD_TOKEN"))
        except Exception as e:
            logger.error(f"❌ Bot failed to start: {e}")

if __name__ == "__main__":
    asyncio.run(main())
