import yt_dlp
import discord
from discord import FFmpegPCMAudio
from discord import FFmpegAudio
from discord import FFmpegOpusAudio

queues = {}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

def get_playlist(query):
    ydl_opts = {
        'format': 'bestaudio',
        'quiet': True,
        'noplaylist': False
    }
    if not query.startswith("http"):
        query = f"ytsearch:{query}"
        ydl_opts['noplaylist'] = True   
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        # No URL
        if 'entries' in info and ydl_opts.get('noplaylist'):
            entry = info['entries'][0]
            return [(entry['url'], entry['title'])]
        # PlayList URL
        elif 'entries' in info:
            return [(entry['url'], entry['title']) for entry in info['entries']]
        # Single Video URL
        else:
            return [(info['url'], info['title'])]
def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

def clean_queue(guild_id):
    queues[guild_id] = []

def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if len(queue) > 0:
        url, title = queue.pop(0)
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
            after=lambda e: play_next(ctx)
        )
