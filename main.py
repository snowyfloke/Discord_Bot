import os
import time
import threading
import logging
import discord

from discord.ext import tasks
from discord.ext import commands
from dotenv import load_dotenv


# Discord Bot Auth
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
# The bot later gets activated by the line "bot.run(DISCORD_TOKEN)"

# Ping command, useful for testing purposes, and learning how to make new commands :3
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! | {round(bot.latency * 1000)}ms!")
# Bot Innit
bot.run(DISCORD_TOKEN)
