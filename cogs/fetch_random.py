import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

# Scryfall's endpoint for looking up a random card
SCRYFALL_NAMED_URL = "https://api.scryfall.com/cards/random"

# Headers provided for Scryfall API Policy
HEADERS = {
    "User-Agent":"DiscordCardBot/0.5",
    "Accept":"application/json",
}

class RandomCard(commands.Cog):
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

    # Slash Command: /random
    @app_commands.command(name="random", description="Fetch a Random MTG Card")
    async def card(self, interaction: discord.Interaction):
        # Defers the response, allowing for processing time
        # Allows for a longer than 3 second response time
        await interaction.response.defer()

        # Make the GET Request to Scryfall
        # `async with` is key to close the response once done reading
        async with self.session.get(SCRYFALL_NAMED_URL, params={}) as resp:
            if resp.status != 200:
                await interaction.followup.send(f"Scryfall returned an unexpected error. Error Code {resp.status}")
                return
            data = await resp.json()

        # Build a Discord embed (card like structure for the card)
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
    await bot.add_cog(RandomCard(bot))