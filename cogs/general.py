import discord
from discord import app_commands
from discord.ext import commands


# A Cog is a class that groups related commands together.
# Inheriting from commands.Cog registers it with the bot framework.
class General(commands.Cog):

    # Called when the cog is loaded. Stores a reference to the bot so commands can use it.
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Registers this method as a slash command named /ping.
    # The description string is what Discord shows users in the / menu.
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        # interaction.response.send_message sends a reply visible in the channel.
        # bot.latency is in seconds, so we multiply by 1000 to get milliseconds.
        await interaction.response.send_message(
            f"Pong! {round(self.bot.latency * 1000)}ms"
        )


# Required by discord.py — called automatically when main.py loads this file.
# Registers the cog with the bot so its commands become active.
async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
