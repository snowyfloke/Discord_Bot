import asyncio
import os
import discord
import uvicorn

from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from music import app as fastapi_app, configure_bot_api
from lang import load_langs, save_langs, get_user_lang, get_msg

print(discord.__version__)
print(discord.__file__)

# Discord Bot Auth
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


class HelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Bot Help")
        for cog, cmds in mapping.items():
            embed.add_field(name=cog.qualified_name, value=f"{len(cmds)} commands")
        channel = self.get_destination()
        await channel.send(embed=embed)


@bot.event
async def on_ready():
    try:  # If bot can connect to discord, send confirmation on terminal
        print("Discord bot successfully connected!")
    except Exception as e:
        print(f"[!] couldn't connect, an Error occurred! Error: {e}")

    try:  # Connect to the Cogs, such as "music-commands.py".
        for cog in os.listdir("./cogs"):
            if cog.endswith("commands.py"):
                await bot.load_extension(f"cogs.{cog[:-3]}")
        print("Cogs loaded!")
    except Exception as e:
        print(f"Failed to load cogs: {e}")

    try:  # Sync commands to Discord (for slash commands)
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# Ping command
@bot.hybrid_command()
async def ping(ctx):
    """Pings the Bot!"""
    await ctx.send(f"Pong🏓! | {round(bot.latency * 1000)}ms!")
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!ping'")


# Voice Channel Commands
@bot.hybrid_command(aliases=["entrar", "j"])
async def join(ctx):
    """Joins the Call"""
    lang = get_user_lang(ctx.author.id)
    if ctx.author.voice:
        channel = ctx.message.author.voice.channel
        try:
            await channel.connect()
            msg = get_msg(lang, "bot_joined_vc").format(channel_name=channel.name)
            await ctx.send(msg)
        except Exception as e:
            await ctx.send(f"Error: {e}")
    else:
        msg = get_msg(lang, "user_not_in_vc")
        await ctx.send(msg)
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!join'")


@bot.hybrid_command(aliases=["quit", "sair", "q"])
async def leave(ctx):
    """Leaves the Call"""
    lang = get_user_lang(ctx.author.id)
    if ctx.author.voice is None:
        msg = get_msg(lang, "user_not_in_vc")
    elif ctx.voice_client:
        channel = ctx.voice_client.channel
        await ctx.guild.voice_client.disconnect()
        msg = get_msg(lang, "bot_left_vc").format(channel_name=channel.name)
        await ctx.send(msg)
    else:
        msg = get_msg(lang, "bot_not_in_vc")
        await ctx.send(msg)
        print(f"{ctx.author.name} in {ctx.guild.name} typed '!leave'")


# Language Switcher
@bot.hybrid_command(aliases=["language", "lingua", "língua", "l"])
@app_commands.describe(
    language="bot language | supported languages: pt (Portuguese) en (English)"
)
async def lang(ctx, language=None):
    """Switches Bot Language"""
    if language is None:
        await ctx.send("Please provide a language. Example: '!lang pt'")
        return
    elif language not in ["pt-br", "pt-pt", "en"]:
        await ctx.send("Invalid language :( | Available languages: pt-br, pt-pt, en")
        return
    langs = load_langs()
    langs[str(ctx.author.id)] = language
    save_langs(langs)

    lang = get_user_lang(ctx.author.id)
    msg = get_msg(lang, "current_language").format(language=lang)
    await ctx.send(msg)
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!lang'")


# API
async def start_services():
    configure_bot_api(bot)
    uvicorn_config = uvicorn.Config(
        fastapi_app, host="127.0.0.1", port=8000, log_level="info"
    )
    server = uvicorn.Server(uvicorn_config)
    await asyncio.gather(bot.start(DISCORD_TOKEN), server.serve())


if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except KeyboardInterrupt:
        print("Bot manually closed.")
