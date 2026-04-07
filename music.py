import yt_dlp
import discord
from concurrent.futures import ThreadPoolExecutor, as_completed
from discord import FFmpegPCMAudio
from discord import FFmpegAudio
from discord import FFmpegOpusAudio

queues = {}

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

def clean_queue(guild_id):
    queues[guild_id] = []

def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        return
    if len(queue) > 0:
        url, title = queue.pop(0)
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
            after=lambda e: play_next(ctx)
        )