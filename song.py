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

ydl_opts = {
    'format': 'bestaudio',
    'quiet': True,
    'noplaylist': True,
}

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]

def get_audio(query):
    if not query.startswith("http"):
        query = f"ytsearch:{query}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)

        if 'entries' in info:
            info = info['entries'][0]
        return info['url'], info['title']

def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if len(queue) > 0:
        url, title = queue.pop(0)
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
            after=lambda e: play_next(ctx)
        )
