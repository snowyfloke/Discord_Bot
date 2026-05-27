import yt_dlp
import discord
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from discord import FFmpegPCMAudio
from discord import FFmpegAudio
from discord import FFmpegOpusAudio
from lang import get_user_lang

queues = {}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

def get_flat_entries(query): # Only grab basic informations, such as title and YouTube url.
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'noplaylist': False,
        'cookiesfrombrowser': ('chrome',),
    }

    if not query.startswith("http"): # Search
        query = f"ytsearch:{query}"
        ydl_opts['noplaylist'] = True # Disables playlists when searching

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)

        if 'entries' in info and ydl_opts.get('noplaylist'):
            entry = info['entries'][0]
            return [(entry['url'], entry['title'])]  # entry['url'] já é a yt_url aqui
        elif 'entries' in info:
            return [(e['url'], e['title']) for e in info['entries']]
        else:
            return [(info['url'], info['title'])]


async def resolve_ahead(ctx, start=0, count=3):
    queue = get_queue(ctx.guild.id)
    for i in range(start, min(start + count, len(queue))):
        stream_url, title, yt_url = queue[i]
        if stream_url is None:
            if yt_url is None:
                continue  # sem URL nenhuma, não tem o que fazer
            resolved_stream, resolved_title = await asyncio.get_event_loop().run_in_executor(
                None, lambda e=(yt_url, title): resolve_entry(e)
            )
            if i < len(queue) and queue[i][1] == title:
                queue[i] = (resolved_stream, resolved_title, yt_url)

def resolve_entry(entry): # Grab the actual audio from the songs
    url, title = entry
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extractor_args': {
            'youtube': {
                'pot_bgutilhttp': ['base_url=http://127.0.0.1:4416']
            }
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return (info['url'], info['title'])

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

def clean_queue(guild_id):
    queues[guild_id] = []

#TODO: Fix loops
#queue_looped = {}
#loops = {}
#def get_loop(guild_id): 
#    return loops.get(guild_id, False)
#def set_loop(guild_id, value):
#    loops[guild_id] = value
#def get_queue_looped(guild_id):
#    if guild_id not in queue_looped:
#        queue_looped[guild_id] = []
#    return queue_looped[guild_id]

async def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        return
    if len(queue) > 0:
        while queue and queue[0][0] is None:
            await asyncio.sleep(0.5)
        if not queue:
            return
        stream_url, title, yt_url = queue.pop(0)  # agora 3 elementos
        if stream_url is None:
            return
        lang = get_user_lang(ctx.author.id)
        msg = f"Tocando Agora: {title}" if lang == "pt" else f"Now Playing: {title}"
        loop = asyncio.get_event_loop()
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS),
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), loop)
        )
        await ctx.send(msg)
