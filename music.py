import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import discord
from discord import FFmpegAudio, FFmpegOpusAudio, FFmpegPCMAudio
from fastapi import FastAPI
from lang import get_msg, get_user_lang
from pydantic import BaseModel
import yt_dlp

queues = {}

GUILDS = [1279210315409657939, 1435286784584978588]

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

app = FastAPI()


class SongRequest(BaseModel):
    busca: str


bot_instance = None


def configure_bot_api(discord_bot):
    """Função para injetar a instância do bot neste módulo."""
    global bot_instance
    bot_instance = discord_bot


def get_flat_entries(query):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "noplaylist": False,
        "extractor_args": {
            "youtube": {"pot_bgutilhttp": ["base_url=http://127.0.0.1:4416"]}
        },
    }

    if not query.startswith("http"):  # Search
        query = f"ytsearch:{query}"
        ydl_opts["noplaylist"] = True  # Disables playlists when searching

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)

        if "entries" in info and ydl_opts.get("noplaylist"):
            entry = info["entries"][0]
            return [(entry["url"], entry["title"])]
        elif "entries" in info:
            return [(e["url"], e["title"]) for e in info["entries"]]
        else:
            return [(info["url"], info["title"])]


async def resolve_ahead(ctx, start=0, count=3):
    queue = get_queue(ctx.guild.id)
    for i in range(start, min(start + count, len(queue))):
        stream_url, title, yt_url = queue[i]
        if stream_url is None:
            if yt_url is None:
                continue
            (
                resolved_stream,
                resolved_title,
            ) = await asyncio.get_event_loop().run_in_executor(
                None, lambda e=(yt_url, title): resolve_entry(e)
            )
            if i < len(queue) and queue[i][1] == title:
                queue[i] = (resolved_stream, resolved_title, yt_url)


def resolve_entry(entry):
    url, title = entry
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "extractor_args": {
            "youtube": {"pot_bgutilhttp": ["base_url=http://127.0.0.1:4416"]}
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return (info["url"], info["title"])


def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = []
    return queues[guild_id]


def clean_queue(guild_id):
    queues[guild_id] = []


async def api_song_proccess(busca: str, guild_id: int):
    if bot_instance is None:
        print(
            "[ERROR] [API] Discord bot instance was NOT configured via configure_bot_api()."
        )
        return

    guild = bot_instance.get_guild(guild_id)
    if not guild or not guild.voice_client:
        print(f"[API] Bot isn't connected in any voice chat inside guild {guild_id}.")
        return

    loop = asyncio.get_event_loop()

    entries = await loop.run_in_executor(None, get_flat_entries, busca)
    if not entries:
        return

    queue = get_queue(guild_id)
    first_index = len(queue)

    for url, title in entries:
        queue.append((None, title, url))

    class SimulatedContext:
        def __init__(self, guild, voice_client, author):
            self.guild = guild
            self.voice_client = voice_client
            self.author = author

        async def send(self, msg):
            print(f"[Discord Bot] {msg}")

    # To satisfy get_user_lang(), the API needs to emulate a ctx.
    ctx_simulated = SimulatedContext(guild, guild.voice_client, guild.me)

    asyncio.create_task(resolve_ahead(ctx_simulated, start=first_index))

    if not guild.voice_client.is_playing() and not guild.voice_client.is_paused():
        await play_next(ctx_simulated)


# HTTP ENDPOINT
@app.post("/play")
async def receive_api_request(request: SongRequest):
    guild_target = None

    if bot_instance:
        for guild_id in GUILDS:
            guild = bot_instance.get_guild(guild_id)
            if guild and guild.voice_client:
                guild_target = guild_id
                break

    if not guild_target:
        guild_target = GUILDS[0]

    asyncio.create_task(api_song_proccess(request.busca, guild_target))
    return {
        "status": "sucesso",
        "mensagem": f"Pedido enviado para a guilda {guild_target}.",
    }


async def play_next(ctx):
    queue = get_queue(ctx.guild.id)
    if ctx.voice_client is None or not ctx.voice_client.is_connected():
        return
    if len(queue) > 0:
        while queue and queue[0][0] is None:
            await asyncio.sleep(0.5)
        if not queue:
            return
        stream_url, title, yt_url = queue.pop(0)
        if stream_url is None:
            return
        lang = get_user_lang(ctx.author.id)
        msg = get_msg(lang, "now_playing").format(track_title=title)
        loop = asyncio.get_event_loop()
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS),
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), loop),
        )
        await ctx.send(msg)
