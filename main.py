import os
import time
import threading
import logging
import discord
import asyncio

from discord.ext import tasks
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord import FFmpegAudio
from discord import FFmpegOpusAudio
from discord import Color
from dotenv import load_dotenv

from song import get_audio

# Discord Bot Auth
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix = "!", help_command=None, intents = intents)
# The bot later gets activated by the line "bot.run(DISCORD_TOKEN)"

@bot.event
async def on_ready():
    try: # If bot can connect to discord

        print('Discord bot succesfully connected!')
    except Exception as e:
        print(f"[!] couldn't connect, an Error occured! Error: {e}")

# Ping command, useful for testing purposes, and learning how to make new commands :3
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! | {round(bot.latency * 1000)}ms!")

# Voice Channel Commands (Useful for other future commands)
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        try:
            await channel.connect()
            await ctx.send(f"Joined {channel.name}")
        except Exception as e:
            await ctx.send(f"Error: {e}")
    else:
        await ctx.send("You're not in a voice channel.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        channel = ctx.voice_client.channel
        await ctx.guild.voice_client.disconnect()
        await ctx.send(f"Left channel {channel.name}")
    else:
        await ctx.send("I'm not in a voice_channel.")

# Song Commands
queue = []

def play_next(ctx):
    if len(queue) > 0:
        url, title = queue.pop(0)
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(url),
            after=lambda e: play_next(ctx)
        )

@bot.command()
async def play(ctx,*,query):
    url, title = await asyncio.get_event_loop().run_in_executor(None, lambda: get_audio(query))
    queue.append((url, title))
    position = len(queue)
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
        return
    if ctx.voice_client is None:
        channel = ctx.message.author.voice.channel
        try:
            await channel.connect()
        except Exception as e:
            await ctx.send(f"Error: {e}")
    if ctx.voice_client.is_playing():
        await ctx.send(f"Added to queue at position {position}: {title}")
    else:
        await ctx.send(f"Now Playing: {title}")
        play_next(ctx)

@bot.command()
async def pause(ctx):
    if ctx.voice_client is None:
        await ctx.send("I'm not playing anything.")
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
    if ctx.voice_client.is_paused():
        await ctx.send("I already paused the Music.")
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused the Music.")

@bot.command()
async def stop(ctx):
    if ctx.voice_client is None:
        await ctx.send("I'm not playing anything.")
    elif ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
    else:
        ctx.voice_client.stop()
        ctx.voice_client.disconnect()
        await ctx.send("I stopped the playback.")

@bot.command()
async def queue_list(ctx):
    if len(queue) == 0:
        await ctx.send("The queue is empty.")
        return
    msg = "\n".join([f"{i+1}. {title}" for i, (url, title) in enumerate(queue)])
    await ctx.send(msg)

@bot.command()
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

# Bot Innit
bot.run(DISCORD_TOKEN)
