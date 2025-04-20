import discord
from discord.ext import commands

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setup_server")
    async def setup_server(self, ctx):
        # Create roles
        roles = ['SC', 'Military', 'Police', 'CATS', 'Others']
        for role_name in roles:
            existing_role = discord.utils.get(ctx.guild.roles, name=role_name)
            if not existing_role:
                await ctx.guild.create_role(name=role_name)
                await ctx.send(f"Role `{role_name}` created!")

        # Create categories
        categories = ['SC', 'Military', 'Police', 'CATS', 'General']
        for category_name in categories:
            existing_category = discord.utils.get(ctx.guild.categories, name=category_name)
            if not existing_category:
                await ctx.guild.create_category(name=category_name)
                await ctx.send(f"Category `{category_name}` created!")

        # Create text and voice channels in categories
        for category_name in categories:
            category = discord.utils.get(ctx.guild.categories, name=category_name)
            if category:
                await ctx.guild.create_text_channel(f"{category_name}-general", category=category)
                await ctx.guild.create_voice_channel(f"{category_name}-voice", category=category)
                await ctx.send(f"Channels created under `{category_name}` category!")

        await ctx.send("Server setup complete.")

# Setup function to add this cog to the bot
def setup(bot):
    bot.add_cog(Setup(bot))
