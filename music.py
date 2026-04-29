import yt_dlp
import discord
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from discord import FFmpegPCMAudio
from discord import FFmpegAudio
from discord import FFmpegOpusAudio
from lang import get_user_lang

queues = {}
queue_looped = {}
loops = {}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}


def get_flat_entries(query):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,  # only fetch metadata, no stream URLs
        'noplaylist': False,
        'cookiesfrombrowser': ('chrome',),
    }

    if not query.startswith("http"):
        query = f"ytsearch:{query}"
        ydl_opts['noplaylist'] = True

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)

        if 'entries' in info and ydl_opts.get('noplaylist'):
            entry = info['entries'][0]
            return [(entry['url'], entry['title'])]
        elif 'entries' in info:
            return [(e['url'], e['title']) for e in info['entries']]
        else:
            return [(info['url'], info['title'])]


def resolve_entry(entry):
    url, title = entry
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return (info['url'], info['title'])

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

def get_queue_looped(guild_id):
    if guild_id not in queue_looped:
        queue_looped[guild_id] = []
    return queue_looped[guild_id]

def clean_queue(guild_id):
    queues[guild_id] = []

def get_loop(guild_id):
    return loops.get(guild_id, False)

def set_loop(guild_id, value):
    loops[guild_id] = value

async def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        return

    if len(queue) == 0 and get_loop(ctx.guild.id):
        if ctx.guild.id in queue_looped and len(queue_looped[ctx.guild.id]) > 0:
            queues[ctx.guild.id] = queue_looped[ctx.guild.id].copy()
            queue = get_queue(ctx.guild.id)
        else:
            return
    if len(queue) > 0:
        while queue and queue[0][0] is None:
            await asyncio.sleep(0.5)
        if not queue:
            return
        current = queue[0][1]
        lang = get_user_lang(ctx.author.id)
        msg = f"Tocando Agora: {current}" if lang == "pt" else f"Now Playing: {current}"
        loop = asyncio.get_event_loop()
        url, title = queue.pop(0)

        if url is None:
            return

        ctx.voice_client.play(
            discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), loop)
        )
        await ctx.send(f"Now Playing: {current}")
