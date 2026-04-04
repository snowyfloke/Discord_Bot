import os
import time
import threading
import logging
import discord
import asyncio
import json
import typing

from typing import Annotated
from discord.ext import tasks
from discord.ext import commands
from discord import Color
from dotenv import load_dotenv

class Music(commands.Cog):
    """
        This is the music category for the bot, you can use it's commands to play music in a voice channel!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["tocar", "sr"])
    async def play(self,ctx,*,query):
        """
            Plays a Song on a VC!
            
            Can be used to either search a song by title, add a song via YouTube URL, or add a whole playlist!
            
            Syntax: !play <query>
            
            Examples:
            !play yellow
            !play https://www.youtube.com/watch?v=ojSmc7s1rgU
            !play https://youtube.com/playlist?list=OLAK5uy_m4lOn8HJoLfTETxg2d6QouxcQd3nM4Gf0&si=3gwvlKZ7G6kyBI1N
        """
        lang = get_user_lang(ctx.author.id)
        tracks = await asyncio.get_event_loop().run_in_executor(None, lambda: get_playlist(query))
        queue = get_queue(ctx.guild.id)
        position = len(queue)
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

    @commands.command(aliases=["pausar", "p"])
    async def pause(self, ctx):
        """
            Pauses the Song
        """
        lang = get_user_lang(ctx.author.id)
        msg = ""
        if ctx.voice_client is None:
            msg = "Não estou tocando nada..." if lang == "pt" else "I'm not playing anything..."
            await ctx.send(msg)
            return
        elif ctx.author.voice is None:
            msg="Você não está em nenhuma call..." if lang == "pt" else "You're not in a voice channel..."
            await ctx.send(msg)
            return
        elif ctx.voice_client.is_paused():
            msg="A música já estava pausada..." if lang == "pt" else "The song was already paused..."
            await ctx.send(msg)
            return
        elif ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            msg="Pausei a música :)" if lang == "pt" else "I paused the music :)"
            await ctx.send(msg)
        print(f"{ctx.author.name} in {ctx.guild.name} typed '!pause'")

    @commands.command(aliases=['unpause', 'continue', 'despause', 'despausar'])
    async def resume(self, ctx):
        """
            Resumes the Song
        """
        lang = get_user_lang(ctx.author.id)
        if ctx.voice_client is None:
            msg = "Não estou tocando nada..." if lang == "pt" else "I'm not playing anything..."
            await ctx.send(msg)
            return
        elif ctx.author.voice is None:
            msg="Você não está em nenhuma call..." if lang == "pt" else "You're not in a voice channel..."
            await ctx.send(msg)
            return
        elif ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            msg="Música voltou a tocar!" if lang == "pt" else "The song was resumed!"
            await ctx.send(msg)
            return
        else:
            msg="A música já estava tocando..." if lang == "pt" else "The song was already playing..."
            await ctx.send(msg)
        print(f"{ctx.author.name} in {ctx.guild.name} typed '!resume'")

    @commands.command(aliases=["parar", "s"])
    async def stop(self, ctx):
        """
            Stops the Current Song
        """
        lang = get_user_lang(ctx.author.id)
        if ctx.voice_client is None:
            msg = "Não estou tocando nada..." if lang == "pt" else "I'm not playing anything..."
            await ctx.send(msg)
            return
        elif ctx.author.voice is None:
            msg="Você não está em nenhuma call..." if lang == "pt" else "You're not in a voice channel..."
            await ctx.send(msg)
            return
        else:
            await ctx.voice_client.disconnect()
            clean_queue(ctx.guild.id)
            msg = "Parei a reprodução :)" if lang == "pt" else "I stopped the playback :)"
            await ctx.send(msg)
        print(f"{ctx.author.name} in {ctx.guild.name} typed '!stop'")

    @commands.command(aliases=["fila"])
    async def queue(self, ctx):
        """
            Shows the Queue
        """
        queue = get_queue(ctx.guild.id)
        lang = get_user_lang(ctx.author.id)
        if len(queue) == 0:
            msg = "A fila está vazia..." if lang == "pt" else "The queue is empty..."
            await ctx.send(msg)
            return
        msg = "\n".join([f"{i+1}. {title}" for i, (url, title) in enumerate(queue)])
        await ctx.send(msg)
        print(f"{ctx.author.name} in {ctx.guild.name} typed '!queue'")

    @commands.command(aliases=["pular"])
    async def skip(self, ctx):
        """
            Skips the Current Song
        """
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        print(f"{ctx.author.name} in {ctx.guild.name} typed '!skip'")

    @commands.command(aliases=["limpar"])
    async def clean(self, ctx):
        """
            Cleans the Queue
        """
        lang = get_user_lang(ctx.author.id)
        queue = get_queue(ctx.guild.id)
        if len(queue) == 0:
            msg = "A fila está vazia..." if lang == "pt" else "The queue is empty..."
            await ctx.send(msg)
        else:
            clean_queue(ctx.guild.id)
            msg = "Esvaziei a fila!" if lang == "pt" else "Cleaned the queue!"
            await ctx.send(msg)
        print(f"{ctx.author.name} in {ctx.guild.name} typed '!clean'")

async def setup(bot):
    await bot.add_cog(Music(bot))
