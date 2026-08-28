from seat_scrapper import greet 

import discord
from discord.ext import commands, tasks

intents = discord.intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
BOT_TOKEN = ""

@tasks.loop(seconds=30.0)
async def search_for_seatings():
    
    channel_id = getattr(search_for_seatings, "target_channel_id", None)
    crns = getattr(search_for_seatings, "crns", [])
    
    if channel_id is None:
        return
    
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("🔔 The polling loop is running.")


@bot.command
async def remove_class(ctx, crn: int):
    
    if not search_for_seatings.is_running():
        return
    
    crns = getattr(search_for_seatings, "crns", [])

    if crn in crns:
        crns.remove(crn)
        
    search_for_seatings.crns = crns
    
@bot.command
async def add_class(ctx, crn: int):
    
    if not search_for_seatings.is_running():
        return

    crns = getattr(search_for_seatings, "crns", [])
    crns.append(crn)
    
    search_for_seatings.crns = crns
    
@bot.command
async def stop_hunt(ctx):
    
    if search_for_seatings.is_running():
        search_for_seatings.stop()

@bot.command
async def begin_hunt(ctx, *crns, loop_interval=30.0):
    
    search_for_seatings.change_interval(seconds=loop_interval)
    search_for_seatings.target_channel_id = ctx.channel_id
    search_for_seatings.crns = crns
    
    if not search_for_seatings.is_running():
        search_for_seatings.start()

""""

@bot.command
async def pause_hunt(ctx):
    pass

@bot.command
async def resume_hunt(ctx):
    pass
    
"""

bot.run(BOT_TOKEN)

