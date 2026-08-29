from seat_scrapper import find_seats 

import os
from dotenv import load_dotenv

import discord
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()
BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Connected to {len(bot.guilds)} server(s):")

    for guild in bot.guilds:
        print(f"  - {guild.name} ({guild.id})")
        
    for command in bot.commands:
        print(f"  !{command.name}")
        
@tasks.loop(minutes=1.0)
async def search_for_seatings():
    
    channel_id = getattr(search_for_seatings, "target_channel_id", None)
    crns = getattr(search_for_seatings, "crns", [])
    
    if channel_id is None:
        return
    
    channel = bot.get_channel(channel_id)
    if channel:
        for crn in crns:
            class_info = await find_seats(crn)
            
            if class_info["left"] > 0:
                await channel.send(f"({class_info['left']} / {class_info['total']}) {class_info['name']}")
            else:
                await channel.send(f"({class_info['left']} / {class_info['total']}) {class_info['name']}")


@bot.command()
async def remove_class(ctx, crn: str):
    
    if not search_for_seatings.is_running():
        return
    
    crns = getattr(search_for_seatings, "crns", [])

    if crn in crns:
        crns.remove(crn)
        
    search_for_seatings.crns = crns
    
@bot.command()
async def add_class(ctx, crn: str):
    
    if not search_for_seatings.is_running():
        return

    crns = getattr(search_for_seatings, "crns", [])
    crns.append(crn)
    
    search_for_seatings.crns = crns
    
@bot.command()
async def stop_hunt(ctx):
    
    if search_for_seatings.is_running():
        search_for_seatings.stop()

@bot.command()
async def begin_hunt(ctx, loop_interval: float = 1.0, *crns):
    
    search_for_seatings.change_interval(minutes=loop_interval)
    search_for_seatings.target_channel_id = ctx.channel.id
    search_for_seatings.crns = crns
    
    if not search_for_seatings.is_running():
        search_for_seatings.start()

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")
     
bot.run(BOT_TOKEN)

