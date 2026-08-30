import discord
from discord import app_commands
from discord.ext import commands

import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# -----------------------------
# Sync slash commands
# -----------------------------

@bot.event
async def setup_hook():
    synced = await bot.tree.sync()

    print(f"Synced {len(synced)} slash command(s):")

    for command in synced:
        print(f"  /{command.name}")


# -----------------------------
# Bot ready
# -----------------------------

@bot.event
async def on_ready():
    print(f"\nLogged in as {bot.user} (ID: {bot.user.id})")
    print(f"Connected to {len(bot.guilds)} server(s):")

    for guild in bot.guilds:
        print(f"  - {guild.name} ({guild.id})")


# -----------------------------
# Slash command
# -----------------------------

@bot.tree.command(
    name="mycommand",
    description="Do something with one or more IDs"
)
async def mycommand(
    interaction: discord.Interaction,
    ids: str
):
    # Split the input by spaces
    id_list = ids.split()

    # Example validation
    if not id_list:
        await interaction.response.send_message(
            "You need to provide at least one ID.",
            ephemeral=True
        )
        return

    # Make sure every value is numeric
    invalid_ids = [value for value in id_list if not value.isdigit()]

    if invalid_ids:
        await interaction.response.send_message(
            f"Invalid ID(s): {', '.join(invalid_ids)}",
            ephemeral=True
        )
        return

    # Convert them to integers if that's what you need
    id_list = [int(value) for value in id_list]

    print(f"Received IDs: {id_list}")

    await interaction.response.send_message(
        f"Received {len(id_list)} ID(s): `{', '.join(map(str, id_list))}`"
    )


    
# -----------------------------
# Start bot
# -----------------------------

bot.run(BOT_TOKEN)