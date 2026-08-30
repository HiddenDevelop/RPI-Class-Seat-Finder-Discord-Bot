import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

from seat_scrapper import find_seats 

import re
import asyncio

import discord
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

guild_hunts = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Connected to {len(bot.guilds)} server(s):")

    for guild in bot.guilds:
        print(f"  - {guild.name} ({guild.id})")
        
    for command in bot.commands:
        print(f"  !{command.name}")
        
    synced = await bot.tree.sync()

    print(f"Synced {len(synced)} slash command(s):")

    for command in synced:
        print(f"  /{command.name}")


def compare_class_states(class_info_1, class_info_2):
    return class_info_1['left'] == class_info_2['left'] and class_info_1['total'] == class_info_2['total'] and class_info_1['name'] == class_info_2['name']

async def search_for_seatings(guild_id):
    
    sleep_time = 60
    
    while guild_id in guild_hunts:
        
        hunt = guild_hunts[guild_id]
        
        channel_id = hunt["channel_id"]
        crns = hunt["crns"]
        
        channel = bot.get_channel(channel_id)

        if channel is None:
            print(f"Could not find channel for guild {guild_id}.")
            await asyncio.sleep(sleep_time)
            return
        
        for crn in crns:
            try:
                class_info = await find_seats(crn)
                previous_state = hunt["class_states"].get(crn)
                
                if (previous_state is None) or (not compare_class_states(previous_state, class_info)):
                    if class_info["left"] > 0:
                        await channel.send(f"@everyone **Register Now!**\nSeat found for {class_info['name']}  :raised_hands:  ({class_info['left']} / {class_info['total']})")
                    else:
                        await channel.send(f"No seats found for {class_info['name']}  😢  ({class_info['left']} / {class_info['total']})")
                else:
                    print("First time observing state or duplicate state seen.")
                    
                hunt["class_states"][crn] = class_info
                
            except Exception as e:
                print(f"Error checking for CRN {crn} in guild {guild_id}: {e}")
                
    asyncio.sleep(sleep_time)
    
@bot.tree.command(name="remove_class", description="Remove class from ongoing hunt.")
async def remove_class(interaction: discord.Interaction, crn: str):
    
    if not search_for_seatings.is_running():
        return
    
    crns = getattr(search_for_seatings, "crns", [])

    if crn in crns:
        crns.remove(crn)
        
    search_for_seatings.crns = crns
    
@bot.tree.command(name="add_class", description="Add class to ongoing hunt.")
async def add_class(interaction: discord.Interaction, crn: str):
    
    if not search_for_seatings.is_running():
        return

    crns = getattr(search_for_seatings, "crns", [])
    crns.append(crn)
    
    search_for_seatings.crns = crns
    
@bot.tree.command(name="stop_hunt", description="Stop tracking classes.")
async def stop_hunt(interaction: discord.Interaction):
    
    if search_for_seatings.is_running():
        search_for_seatings.stop()


@bot.tree.command(name="begin_hunt", description="Begin tracking class seatings by crn.")
async def begin_hunt(interaction: discord.Interaction, crns: str):
    
    crn_list = re.split(r",\s*|\s+", crns)
    
    if not crn_list:
        await interaction.response.send_message("You need to provide at least one crn.", ephemeral=True)
        return
    
    invalid_crns = [value for value in crn_list if not value.isdigit()]
    
    if invalid_crns:
        await interaction.response.send_message(f"Invalid crn(s): {', '.join(invalid_crns)}", ephemeral=True)
        return
    
    crn_list = [int(value) for value in crn_list]
    
    print(f"Received crns: {crn_list}")
    
    await interaction.response.send_message(f"**Let the Hunt Begin!**\nKeeping an eye out for {len(crn_list)} CRN (s): `{', '.join(map(str, crn_list))}`")
    
    search_for_seatings.change_interval(minutes=1)
    search_for_seatings.target_channel_id = interaction.channel.id
    search_for_seatings.crns = crn_list
    
    if not search_for_seatings.is_running():
        search_for_seatings.start()

@bot.tree.command(name="hunt_status", description="Check hunt status.")
async def hunt_status(interaction: discord.Interaction):
    
    if search_for_seatings.is_running():
        await interaction.response.send_message("Hunt is currently active.")
    else:
        await interaction.response.send_message("Hunt is currently unactive.")

@bot.tree.command(name="ping", description="Verify bot is running.")
async def ping(ctx):
    await ctx.send("Pong! 🏓")
     
bot.run(BOT_TOKEN)

