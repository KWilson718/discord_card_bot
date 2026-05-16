import asyncio
import os

# discord.py — the main library for interacting with the Discord API
import discord
# commands gives us the Bot class and the framework for building command-based bots
from discord.ext import commands
# python-dotenv lets us load variables from a .env file into os.environ
from dotenv import load_dotenv

# Reads the .env file and makes DISCORD_TOKEN available via os.environ
load_dotenv()

# Intents are permissions that tell Discord which events to send to the bot.
# default() includes most standard events (messages, reactions, etc.) but
# excludes privileged ones like reading message content.
intents = discord.Intents.default()
intents.message_content = True  # privileged — must also be enabled in the developer portal

# Create the bot instance. command_prefix sets the prefix for legacy text commands (e.g. !ping).
# Slash commands don't use this, but Bot requires it.
bot = commands.Bot(command_prefix="!", intents=intents)


# This event fires once the bot has successfully connected to Discord and is ready.
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        # --- DEV ONLY: guild-specific sync ---
        # Syncing to a guild is instant. Global sync (no guild arg) takes up to an hour.
        # BEFORE PROD: remove this entire block and replace with `await bot.tree.sync()`
        # Also remove GUILD_ID from .env and clear_global_commands.py can be deleted.
        guild = discord.Object(id=int(os.environ["GUILD_ID"]))
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        # --- END DEV ONLY ---

        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# Scans the cogs/ directory and loads every .py file as a bot extension.
# This means you can add new cogs without touching this file.
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


# Main coroutine — loads cogs then starts the bot using the token from .env.
# Using `async with bot` ensures a clean shutdown when the process exits.
async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.environ["DISCORD_TOKEN"])


# Standard Python entry point guard — only runs when executing this file directly.
if __name__ == "__main__":
    asyncio.run(main())
