import os
import discord

from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

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
# The bot later gets activated by the line "bot.run(DISCORD_TOKEN)"


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
        print("Discord bot succesfully connected!")
    except Exception as e:
        print(f"[!] couldn't connect, an Error occured! Error: {e}")

    try:  # Connect to the Cogs, such as "music-commands.py". This way, files become smaller and more manageable. I strongly advice making new cogs instead of just putting everything here!
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


# Ping command, useful for testing purposes, and learning how to make new commands :3
@bot.hybrid_command()
async def ping(ctx):
    """Pings the Bot!"""
    await ctx.send(f"Pong🏓! | {round(bot.latency * 1000)}ms!")
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!ping'")


# Voice Channel Commands (Useful for other audio-related commands)
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
    """
    Switches Bot Language

    Obs: Does NOT switch !help language (if you know how to do this, please dm @snow_floke)

    Syntax: !lang <lg>

    Supported Languages:
    'pt': Portuguese
    'en': English
    """  # Update this line if you add a new language!
    if language is None:
        await ctx.send("Please provide a language. Example: '!lang pt'")
        return
    elif language not in [
        "pt",
        "en",
    ]:  # To add new languages, just add a new entry to this line!
        await ctx.send(
            "Invalid language :( | Available languages: pt, en"
        )  # Update this one as well!!!
        return
    langs = load_langs()
    langs[str(ctx.author.id)] = language
    save_langs(langs)

    lang = get_user_lang(ctx.author.id)
    msg = get_msg(lang, "current_language").format(language=lang)
    await ctx.send(msg)
    print(f"{ctx.author.name} in {ctx.guild.name} typed '!lang'")


# Bot Innit
bot.run(DISCORD_TOKEN)
