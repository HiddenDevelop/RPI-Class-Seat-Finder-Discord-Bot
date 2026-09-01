import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]

from seat_scrapper import find_seats 

import re
import asyncio

from datetime import datetime, timezone

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

def get_hunt_key(interaction: discord.Interaction):
    if interaction.guild is not None:
        return ("guild", interaction.guild.id)
    
    return ("user", interaction.user.id)

def make_notification_embed(empty, name, left, total, timestamp):
    if empty:
        embed = discord.Embed(
            title=":raised_hands: SEAT AVAILABLE",
            description=f"{name}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🪑 Availability",
            value=f"{left} / {total} seats available",
            inline=False
        )
        
        embed.add_field(
            name="",
            value="👉 **Register now!**",
            inline=False
        )
        
        embed.add_field(
            name="⏱️ Last checked",
            value=f"<t:{timestamp}:F>",
            inline=False
        )
        
        return embed
    else:
        embed = discord.Embed(
            title=":broken_heart: CLASS FULL",
            description=f"{name}",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="🪑 Availability",
            value=f"{left} / {total} seats available",
            inline=False
        )
        
        embed.add_field(
            name="⏱️ Last checked",
            value=f"<t:{timestamp}:F>",
            inline=False
        )
        
        return embed

async def send_notification(channel, new_state, previous_state):
    
    name = new_state["name"]
    left = new_state["left"]
    total = new_state["total"]
    
    if (previous_state is not None) and (previous_state.get("message_id") is not None):
        try:
            message = await channel.fetch_message(previous_state["message_id"])
            
            # notify users that registration is open
            if new_state["left"] > 0:
                await message.edit(embed=make_notification_embed(True, name, left, total, int(datetime.now(timezone.utc).timestamp())))
                new_state["message_id"] = message.id
            # notify users that class section is full
            else:
                await message.edit(embed=make_notification_embed(False, name, left, total, int(datetime.now(timezone.utc).timestamp())))
                new_state["message_id"] = message.id
            return
        
        except Exception as e:
            print("Error while attempting to edit old message: {e}")
    
    # notify users that registration is open
    if new_state["left"] > 0:
        message = await channel.send(embed=make_notification_embed(True, name, left, total, int(datetime.now(timezone.utc).timestamp())))
        new_state["message_id"] = message.id
    # notify users that class section is full
    else:
        message = await channel.send(embed=make_notification_embed(False, name, left, total, int(datetime.now(timezone.utc).timestamp())))
        new_state["message_id"] = message.id
            
async def search_for_seatings(hunt_key):
    
    sleep_time = 20
    
    # polling loop for seat hunt
    while hunt_key in guild_hunts:
        
        hunt = guild_hunts[hunt_key]
        
        channel_id = hunt["channel_id"]
        crns = hunt["crns"]
        
        # verify channel exists
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.NotFound:
            print(f"Channel {channel_id} does not exist.")
            await asyncio.sleep(sleep_time)
            continue
        except discord.Forbidden:
            print(f"Bot cannot access channel {channel_id}.")
            await asyncio.sleep(sleep_time)
            continue
        except discord.HTTPException as e:
            print(f"Error fetching channel {channel_id}: {e}")
            await asyncio.sleep(sleep_time)
            continue
        
        # parse through CRN(s) and pull information on them
        for crn in crns:
            try:
                class_info = await find_seats(crn)
                previous_state = hunt["class_states"].get(crn)
                
                await send_notification(channel, class_info, previous_state)
                    
                # update CRN state
                hunt["class_states"][crn] = class_info
                
            except Exception as e:
                print(f"Error checking for CRN {crn} in guild {hunt_key}: {e}")
                
        await asyncio.sleep(sleep_time)
    
@bot.tree.command(name="remove_class", description="Remove class from ongoing hunt.")
async def remove_class(interaction: discord.Interaction, crn: str):
    
    hunt_key = get_hunt_key(interaction)

    if hunt_key not in guild_hunts:
        await interaction.response.send_message(f"There is no hunt on this server.")
        return

    if crn in guild_hunts[hunt_key]["crns"]:
        guild_hunts[hunt_key]["crns"].remove(crn)
    
    await interaction.response.send_message(f"Removed CRN {crn} to hunt.")
    
    
@bot.tree.command(name="add_class", description="Add class to ongoing hunt.")
async def add_class(interaction: discord.Interaction, crn: str):
    
    hunt_key = get_hunt_key(interaction)

    if hunt_key not in guild_hunts:
        await interaction.response.send_message(f"There is no hunt on this server.")
        return

    hunt = guild_hunts[hunt_key]
    
    if crn in hunt["crns"]:
        await interaction.response.send_message(f"CRN {crn} already in hunt.")
        return
     
    hunt["crns"].append(crn)
    await interaction.response.send_message(f"Added CRN {crn} to hunt.")

    
@bot.tree.command(name="stop_hunt", description="Stop tracking classes.")
async def stop_hunt(interaction: discord.Interaction):
    
    hunt_key = get_hunt_key(interaction)
    
    if hunt_key not in guild_hunts:
        await interaction.response.send_message(f"There is no hunt on this server.")
        return
    
    task = guild_hunts[hunt_key]["task"]
    
    if task is not None:
        task.cancel()
        
    del guild_hunts[hunt_key]
    
    await interaction.response.send_message(f"The hunt has been stopped.")


@bot.tree.command(name="begin_hunt", description="Begin tracking class seatings by crn.")
async def begin_hunt(interaction: discord.Interaction, crns: str):
    
    hunt_key = get_hunt_key(interaction)
    
    # input validation
    
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
    
    # setting up guild hunt
    
    # cancel existing hunt
    if hunt_key in guild_hunts:
        
        old_task = guild_hunts[hunt_key]["task"]

        if old_task is not None:
            old_task.cancel()

    guild_hunts[hunt_key] = {
        "channel_id" : interaction.channel.id,
        "crns" : crn_list,
        "class_states" : {},
        "task" : None
    }
    
    # create task for this guild
    task = asyncio.create_task( search_for_seatings(hunt_key) )
    
    guild_hunts[hunt_key]["task"] = task
    
    await interaction.response.send_message(f"**Let the Hunt Begin!**\nKeeping an eye out for {len(crn_list)} CRN (s): `{', '.join(map(str, crn_list))}`")

@bot.tree.command(name="hunt_status", description="Check hunt status.")
async def hunt_status(interaction: discord.Interaction):
    
    hunt_key = get_hunt_key(hunt_key)
    
    if hunt_key in guild_hunts and guild_hunts[hunt_key]["task"] is not None:
        await interaction.response.send_message("Hunt is currently active.")
    else:
        await interaction.response.send_message("Hunt is currently unactive.")
        

@bot.tree.command(name="ping", description="Verify bot is running.")
async def ping(ctx):
    await ctx.send("Pong! 🏓")
     
bot.run(BOT_TOKEN)

