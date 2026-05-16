import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# Scryfall's endpoint for looking up a card by name.
# The "fuzzy" parameter means close-enough matches work (e.g. "lightning bolt" finds "Lightning Bolt").
SCRYFALL_NAMED_URL = "https://api.scryfall.com/cards/named"

# Scryfall asks that all API clients identify themselves via User-Agent.
HEADERS = {
    "User-Agent": "DiscordCardBot/1.0",
    "Accept": "application/json",
}


class Cards(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Placeholder — the actual session is created in cog_load below.
        self.session: aiohttp.ClientSession | None = None

    # Called automatically by discord.py after the cog is added to the bot.
    # We create the aiohttp session here rather than in __init__ because
    # creating it requires an active asyncio event loop.
    async def cog_load(self):
        self.session = aiohttp.ClientSession(headers=HEADERS)

    # Called automatically when the cog is removed or the bot shuts down.
    # Always close the session to avoid resource leaks.
    async def cog_unload(self):
        if self.session:
            await self.session.close()

    # Slash command: /card <name>
    # The describe decorator sets the help text shown for the argument in Discord's UI.
    @app_commands.command(name="card", description="Look up a Magic: The Gathering card by name")
    @app_commands.describe(name="The card name to search for")
    async def card(self, interaction: discord.Interaction, name: str):
        # Defers the response — tells Discord "I got it, give me a moment."
        # Required when the API call might take longer than Discord's 3-second response window.
        await interaction.response.defer()

        # Make the GET request to Scryfall. `async with` ensures the response is
        # properly closed after we're done reading it.
        async with self.session.get(SCRYFALL_NAMED_URL, params={"fuzzy": name}) as resp:
            if resp.status == 404:
                await interaction.followup.send(f"No card found for **{name}**.")
                return
            if resp.status != 200:
                await interaction.followup.send("Scryfall returned an unexpected error. Try again later.")
                return
            # Parse the response body as JSON into a Python dict.
            data = await resp.json()

        # Build a Discord embed (a formatted card-like message) with the card's details.
        embed = discord.Embed(
            title=data["name"],
            url=data["scryfall_uri"],  # links to the card's page on Scryfall
            color=discord.Color.blue(),
        )

        embed.add_field(name="Mana Cost", value=data.get("mana_cost", "N/A"), inline=True)
        embed.add_field(name="Type", value=data.get("type_line", "N/A"), inline=True)
        # oracle_text is the rules text on the card
        embed.add_field(name="Oracle Text", value=data.get("oracle_text", "N/A"), inline=False)

        # Power and toughness only exist on creatures, so we check before adding.
        if "power" in data:
            embed.add_field(name="P/T", value=f"{data['power']}/{data['toughness']}", inline=True)

        # image_uris won't exist on double-faced cards (those use card_faces instead).
        # We only set the thumbnail if this is a normal single-faced card.
        if "image_uris" in data:
            embed.set_thumbnail(url=data["image_uris"]["normal"])

        # followup.send is used after a defer() instead of the normal response.send_message.
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Cards(bot))
