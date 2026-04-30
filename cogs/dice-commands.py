import random
import os
import discord

from discord.ext import commands

class Dice(commands.Cog):
    """
        This is the dice category for the bot, you can use it's commands to roll dice!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        content = message.content

        if content.startswith("d"):
            dice_part = content[1:]

            if dice_part.isdigit():
                sides = int(dice_part)
                result = random.randint(1, sides)
                await message.channel.send(f"🎲 You rolled a d{sides}: **{result}**")
            else:
                return
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(Dice(bot))
