import os
import time
import threading
import logging
import discord
import discord.ui
import asyncio
import json

from discord.ext import tasks
from discord.ext import commands
from dotenv import load_dotenv

from music import resolve_entry, get_flat_entries, play_next, get_queue, clean_queue
from lang import load_langs, save_langs, get_user_lang

print(discord.__version__)
print(discord.__file__)

# Discord Bot Auth
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix = "!", intents = intents)
# The bot later gets activated by the line "bot.run(DISCORD_TOKEN)"

class HelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Bot Help")
        for cog, cmds in mapping.items():
            embed.add_field(
                name = cog.qualified_name,
                value = f"{len(cmds)} commands"
            )
        channel = self.get_destination()
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    try: # If bot can connect to discord

        print('Discord bot succesfully connected!')
    except Exception as e:
        print(f"[!] couldn't connect, an Error occured! Error: {e}")

    try:
        for cog in os.listdir('./cogs'):
            if cog.endswith('commands.py'):
                await bot.load_extension(f'cogs.{cog[:-3]}')
            print("Cogs loaded!")
    except Exception as e:
        print(f"Failed to load cogs: {e}")

# Ping command, useful for testing purposes, and learning how to make new commands :3
@bot.command()
async def ping(ctx):
    """ Pings the Bot! """
    await ctx.send(f"Pong🏓! | {round(bot.latency * 1000)}ms!")
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!ping'")

# Voice Channel Commands (Useful for other audio-related commands)
@bot.command(aliases=["entrar", "j"])
async def join(ctx):
    """Joins the Call"""
    lang = get_user_lang(ctx.author.id)
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        try:
            await channel.connect()
            msg = f"Entrei em {channel.name}" if lang == "pt" else f"Joined {channel.name}"
            await ctx.send(msg)
        except Exception as e:
            await ctx.send(f"Error: {e}")
    else:
        msg = "Você não está em uma call..." if lang == "pt" else "You're not in a voice channel..."
        await ctx.send(msg)
    print(f"{ctx.author.name} in { ctx.guild.name} typed '!join'")

@bot.command(aliases=["quit", "sair", "q"])
async def leave(ctx):
    """Leaves the Call"""
    lang = get_user_lang(ctx.author.id)
    if ctx.author.voice is None:
        msg = "Você não está em nenhuma call..." if lang == "pt" else "You're not in a voice channel..."
    elif ctx.voice_client:
        channel = ctx.voice_client.channel
        await ctx.guild.voice_client.disconnect()
        msg = f"Saí da call {channel.name}" if lang == "pt" else f"Left channel {channel.name}"
        await ctx.send(msg)
    else:
        msg = "Eu não estou em nenhuma call..." if lang == "pt" else "I'm not in a voice channel..."
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!leave'")

# Language Switcher
@bot.command(aliases=["language", "lingua", "língua", "l"])
async def lang(ctx, language=None):
    """
        Switches Bot Language

        Obs: Does NOT switch !help language (if you know how to do this, please dm @snow_floke)

        Syntax: !lang <lg>

        Supported Languages:
        'pt': Portuguese
        'en': English
    """
    if language is None:
        await ctx.send("Please provide a language. Example: '!lang pt'")
        return
    elif language not in ["pt", "en"]:
        await ctx.send("Invalid language :( | Available languages: pt, en")
        return
    langs = load_langs()
    langs[str(ctx.author.id)] = language
    save_langs(langs)

    lang = get_user_lang(ctx.author.id)
    msg = f"Língua atual: {language}" if lang == "pt" else f"Current language: {language}"
    await ctx.send(msg)
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!lang'")
# Bot Innit
bot.run(DISCORD_TOKEN)
