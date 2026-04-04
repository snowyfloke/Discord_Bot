import os
import time
import threading
import logging
import discord
import asyncio
import json

from discord.ext import tasks
from discord.ext import commands
from discord import Color
from dotenv import load_dotenv

from song import get_playlist, play_next, get_queue
from lang import load_langs, save_langs, get_user_lang

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
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!ping'")

# Voice Channel Commands (Useful for other audio-related commands)
@bot.command(aliases=["entrar", "j"])
async def join(ctx):
    lang = get_user_lang(ctx.author.id)
    msg = ""
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        try:
            await channel.connect()
            main.pymsg = f"Entrei em {channel.name}" if lang == "pt" else f"Joined {channel.name}"
            await ctx.send(msg)
        except Exception as e:
            await ctx.send(f"Error: {e}")
    else:
        if lang == "pt":
            await ctx.send("Você não está em uma call.")
        else:
            await ctx.send("You're not in a voice channel.")
    print(f"{ctx.author.name} in { ctx.guild.name} typed '!join'")

@bot.command(aliases=["quit", "sair", "q"])
async def leave(ctx):
    lang = get_user_lang(ctx.author.id)
    msg = ""
    if ctx.voice_client:
        channel = ctx.voice_client.channel
        await ctx.guild.voice_client.disconnect()
        msg = f"Saí da call {channel.name}" if lang == "pt" else f"Left channel {channel.name}"
        await ctx.send(msg)
    else:
        msg = "Eu não estou em nenhuma call..." if lang == "pt" else "I'm not in a voice channel..."
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!leave'")
    
# Song Commands
@bot.command(aliases=["tocar", "sr"])
async def play(ctx,*,query):
    lang = get_user_lang(ctx.author.id)
    tracks = await asyncio.get_event_loop().run_in_executor(None, lambda: get_playlist(query))
    queue = get_queue(ctx.guild.id)
    position = len(queue)
    msg = ""
    if ctx.author.voice is None:
        msg = "Você não está em nenhuma call..." if lang == "pt" else "You're not in a voice channel..."
        await ctx.send(msg)
    else:
        if ctx.voice_client is None:
            channel = ctx.message.author.voice.channel
            try:
                await channel.connect()
                msg = f"Entrei em {channel.name}" if lang == "pt" else f"Joined {channel.name}"
                await ctx.send(msg)
            except Exception as e:
                await ctx.send(f"Error: {e}")
        for url, title in tracks:
            queue.append((url, title))
        if len(tracks) > 1:
            msg = f"Adicionadas {len(tracks)} músicas à fila :D" if lang == "pt" else f"Added {len(tracks)} songs to the queue!"
            await ctx.send(msg)
        else:
            msg = f"Adicionada: {tracks[0][1]}" if lang == "pt" else f"Added: {tracks[0][1]}"
            await ctx.send(msg)
            if not ctx.voice_client.is_playing():
                play_next(ctx)
                play_next(ctx)
                msg = f"Tocando Agora: {title}" if lang == "pt" else f"Now Playing: {title}"
                await ctx.send(msg)
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!play'")

@bot.command(aliases=["pausar", "p"])
async def pause(ctx):
    lang = get_user_lang(ctx.author.id)
    msg = ""
    if ctx.voice_client is None:
        msg = "Não estou tocando nada..." if lang == "pt" else "I'm not playing anything..."
        await ctx.send(msg)
        return
    if ctx.author.voice is None:
        msg="Você não está em nenhuma call..." if lang == "pt" else "You're not in a voice channel..."
        await ctx.send(msg)
        return
    if ctx.voice_client.is_paused():
        msg="A música já estava pausada..." if lang == "pt" else "The song was already paused..."
        await ctx.send(msg)
        return
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        msg="Pausei a música :)" if lang == "pt" else "I paused the music :)"
        await ctx.send(msg)
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!pause'")

@bot.command(aliases=["parar", "s"])
async def stop(ctx):
    lang = get_user_lang(ctx.author.id)
    msg = ""
    if ctx.voice_client is None:
        msg = "Não estou tocando nada..." if lang == "pt" else "I'm not playing anything..."
        await ctx.send(msg)
        return
    if ctx.author.voice is None:
        msg="Você não está em nenhuma call..." if lang == "pt" else "You're not in a voice channel..."
        await ctx.send(msg)
        return
    else:
        ctx.voice_client.stop()
        ctx.voice_client.disconnect()
        msg = "Parei a reprodução :)" if lang == "pt" else "I stopped the playback :)"
        await ctx.send(msg)
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!stop'")

@bot.command(aliases=["fila"])
async def queue(ctx):
    queue = get_queue(ctx.guild.id)
    lang = get_user_lang(ctx.author.id)
    msg = ""
    if len(queue) == 0:
        msg = "A fila está vazia..." if lang == "pt" else "The queue is empty..."
        await ctx.send(msg)
        return
    msg = "\n".join([f"{i+1}. {title}" for i, (url, title) in enumerate(queue)])
    await ctx.send(msg)
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!queue'")

@bot.command(aliases=["pular"])
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!skip'")

@bot.command(aliases=["limpar"])
async def clean(ctx):
    lang = get_user_lang(ctx.author.id)
    queue = get_queue(ctx.guild.id)
    if len(queue) == 0:
        msg = "A fila está vazia..." if lang == "pt" else "The queue is empty..."
        await ctx.send(msg)
    else:
        clean_queue(ctx.guild.id)
        msg = "Esvaziei a fila!" if lang == "pt" else "Cleaned the queue!"
        await ctx.send(msg)

# Language Switcher
@bot.command(aliases=["language", "lingua", "língua", "l"])
async def lang(ctx, language=None):
    msg = ""
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
