import yt_dlp
import discord
from discord import FFmpegPCMAudio
from discord import FFmpegAudio
from discord import FFmpegOpusAudio

queues = {}

ydl_opts = {
    'format': 'bestaudio',
    'quiet': True,
    'noplaylist': False,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

def get_playlist(query):
    ydl_playlist_opts = {
        'format': 'bestaudio',
        'quiet': True,
    }
    if not query.startswith("http"):
        query = f"ytsearch:{query}"    
    with yt_dlp.YoutubeDL(ydl_playlist_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info:
            tracks = []
            for entry in info['entries']:
                tracks.append((entry['url'], entry['title']))
            return tracks
        else:
            return info['url'], info['title']

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if len(queue) > 0:
        url, title = queue.pop(0)
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
            after=lambda e: play_next(ctx)
        )
