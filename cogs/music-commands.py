import os
import time
import threading
import logging
import discord
import discord.ui
import asyncio
import json
import typing
import random

from music import resolve_entry, resolve_ahead, get_flat_entries, play_next, get_queue, clean_queue
from lang import load_langs, save_langs, get_user_lang

from typing import Annotated
from discord.ext import tasks
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# ################## #
# QUEUE EMBED CONFIG #
# ################## #

def build_queue_pages(queue, per_page=20): # Change this line if you wish to have more songs on each page!
    pages = []
    for i in range(0, len(queue), per_page):
        chunk = queue[i:i + per_page]
        lines = [f"`{i + j + 1}.` {title}" for j, (stream_url, title, yt_url) in enumerate(chunk)]
        pages.append("\n".join(lines))
    return pages

class QueueView(discord.ui.View):
    def __init__(self, pages, lang):
        super().__init__(timeout=60)
        self.pages = pages
        self.current = 0
        self.lang = lang

    def make_embed(self):
        label = "Fila" if self.lang == "pt" else "Queue"
        embed = discord.Embed(
            title=label,
            description=self.pages[self.current],
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"{self.current + 1}/{len(self.pages)}")
        return embed

    @discord.ui.button(label="⬅", style=discord.ButtonStyle.secondary)
    async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current > 0:
            self.current -=1
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="➡", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current < len(self.pages) -1:
            self.current +=1
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

class Music(commands.Cog):
    """
        This is the music category for the bot, you can use it's commands to play music in a voice channel!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["tocar", "sr"])
    @app_commands.describe(query="Song title or YouTube URL (supports playlists)")
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
        print(f"{ctx.author.name} in {ctx.guild.name} typed '!play {query}'") # LOG
        lang = get_user_lang(ctx.author.id)
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
                    return

            flat_tracks = await asyncio.get_event_loop().run_in_executor(None, lambda: get_flat_entries(query))
            for entry in flat_tracks:
                queue.append((None, entry[1], entry[0]))

            if len(flat_tracks) > 1:
                msg = f"Adicionados {len(flat_tracks)} músicas à fila :D" if lang == "pt" else f"Added {len(flat_tracks)} songs to the queue!"
                await ctx.send(msg)
            else:
                msg = f"Adicionada a Fila: {flat_tracks[0][1]}" if lang == "pt" else f"Added to the Queue: {flat_tracks[0][1]}"
                await ctx.send(msg)

            async def resolve_and_enqueue():
                await resolve_ahead(ctx, start=0, count=3)
                if not ctx.voice_client.is_playing():
                    await play_next(ctx)
                queue = get_queue(ctx.guild.id)
                for i in range(3, len(queue)):
                    if i < len(queue) and queue[i][0] is None:
                        stream_url, title, yt_url = queue[i]
                        url, resolved_title = await asyncio.get_event_loop().run_in_executor(
                            None, lambda e=(yt_url, title): resolve_entry(e)
                        )
                        if i < len(queue) and queue[i][1] == title:
                            queue[i] = (url, resolved_title, yt_url)
            asyncio.create_task(resolve_and_enqueue())

    @commands.hybrid_command(aliases=["pausar", "p"])
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

    @commands.hybrid_command(aliases=['unpause', 'continue', 'despause', 'despausar'])
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

    @commands.hybrid_command(aliases=["parar", "s"])
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

    @commands.hybrid_command(aliases=["fila"])
    async def queue(self, ctx):
        """
            Shows the Queue
        """
        q = get_queue(ctx.guild.id)
        lang = get_user_lang(ctx.author.id)
        if not q:
            msg = "A fila está vazia..." if lang == "pt" else "The queue is empty..."
            await ctx.send(msg)
            return

        pages = build_queue_pages(q)
        view = QueueView(pages, lang)
        await ctx.send(embed=view.make_embed(), view=view)

    @commands.hybrid_command(aliases=["pular"])
    async def skip(self, ctx):
        """
            Skips the Current Song
        """
        lang = get_user_lang(ctx.author.id)
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            msg = "Pulei a música atual!" if lang == "pt" else "Skipped the current song!"
            await ctx.send(msg)
        print(f"{ctx.author.name} in {ctx.guild.name} typed '!skip'")

    @commands.hybrid_command(aliases=["limpar"])
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

    @commands.hybrid_command(aliases=["embaralhar", "aleatorio", "aleatório", "random"])
    async def shuffle(self, ctx):
        """
            Shuffles the queue
        """
        lang = get_user_lang(ctx.author.id)
        queue = get_queue(ctx.guild.id)
        if len(queue) == 0:
            msg = "A fila está vazia..." if lang == "pt" else "The queue is empty..."
            await ctx.send(msg)
        else:
            for i in range(len(queue)):
                stream_url, title, yt_url = queue[i]
                queue[i] = (None, title, yt_url)  # yt_url preservada!

            random.shuffle(queue)            
            
            msg = "Embaralhei a fila :)" if lang == "pt" else "Shuffled the queue :)"
            await ctx.send(msg)

            asyncio.create_task(resolve_ahead(ctx, start=0, count=3))
            async def resolve_rest():
                queue_ref = get_queue(ctx.guild.id)
                for i in range(3, len(queue_ref)):
                    if i < len(queue_ref) and queue_ref[i][0] is None:
                        stream_url, title, yt_url = queue_ref[i]
                        url, resolved_title = await asyncio.get_event_loop().run_in_executor(
                            None, lambda e=(yt_url, title): resolve_entry(e)
                        )
                        if i < len(queue_ref) and queue_ref[i][1] == title:
                            queue_ref[i] = (url, resolved_title, yt_url)
            asyncio.create_task(resolve_rest())

async def setup(bot):
    await bot.add_cog(Music(bot))
