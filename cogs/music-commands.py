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

from music import resolve_entry, get_flat_entries, play_next, get_queue, clean_queue
from lang import load_langs, save_langs, get_user_lang

from typing import Annotated
from discord.ext import tasks
from discord.ext import commands
from dotenv import load_dotenv

def build_queue_pages(queue, per_page=20):
    pages = []
    for i in range(0, len(queue), per_page):
        chunk = queue[i:i + per_page]
        lines = [f"`{i + j + 1}.` {title}" for j, (url, title) in enumerate(chunk)]
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
        print(f"{ctx.author.name} in {ctx.guild.name} typed '!play {query}'")
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

            # Step 1: get flat entry list fast (no stream URL resolution yet)
            flat_tracks = await asyncio.get_event_loop().run_in_executor(None, lambda: get_flat_entries(query))

            if len(flat_tracks) > 1:
                msg = f"Adicionados {len(flat_tracks)} músicas à fila :D" if lang == "pt" else f"Added {len(flat_tracks)} songs to the queue!"
                await ctx.send(msg)
            else:
                await ctx.send(f"Added: {flat_tracks[0][1]}")

            # Step 2: resolve and enqueue in background
            async def resolve_and_enqueue():
                for entry in flat_tracks:
                    url, title = await asyncio.get_event_loop().run_in_executor(None, lambda e=entry: resolve_entry(e))
                    queue.append((url, title))
                    if not ctx.voice_client.is_playing():
                        play_next(ctx)

            asyncio.create_task(resolve_and_enqueue())

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
        q = get_queue(ctx.guild.id)
        lang = get_user_lang(ctx.author.id)
        if not q:
            msg = "A fila está vazia..." if lang == "pt" else "The queue is empty..."
            await ctx.send(msg)
            return

        pages = build_queue_pages(q)
        view = QueueView(pages, lang)
        await ctx.send(embed=view.make_embed(), view=view)

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

    @commands.command(aliases=["embaralhar", "aleatorio", "aleatório", "random"])
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
            random.shuffle(queue)
            msg = "Embaralhei a fila :)" if lang == "pt" else "Shuffled the queue :)"
            await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Music(bot))
