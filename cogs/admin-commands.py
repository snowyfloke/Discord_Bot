import discord
import datetime
from discord.ext import commands
from lang import get_user_lang

class Admin(commands.Cog):
    """
        Server Management Section
        Most commands require admin permissions!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """
            Bans a member!

            Syntax: !ban @user-to-ban <reason>
            If no reason is defined, it defaults to none.
        """
        print("User typed !ban") # LOG
        lang = get_user_lang(ctx.author.id)
        if member.guild_permissions.administrator:
            msg = "Você está tentando banir um admin, n faça isso, ele ficará triste :(" if lang == "pt" else "You're trying to ban an admin, please don't do that, he will be very sad :("
            await ctx.send(msg)
            return

        else:
            await member.ban(reason=reason)
            msg = f"{member} foi banido por {ctx.author}! \n \nMotivo: {reason}" if lang == "pt" else f"{member} has been banned by {ctx.author}! \n \nReason: {reason}"
            await ctx.send(msg)

    @commands.command(aliases=["expulsar"])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, reason=None):
        """
            Kicks a member!

            Syntax: !kick @user-to-kick <reason>
            If no reason is defined, it defaults to none.
        """
        print("User typed !kick") # LOG
        lang = get_user_lang(ctx.author.id)
        if member.guild_permissions.administrator:
            msg = "Você quer chutar um ADM? Que feio!" if lang == "pt" else "You want to kick an admin? MEAN!"
            await ctx.send(msg)
            return
        else:
            await member.kick(reason=reason)
            msg = f"{member} foi expulso por {ctx.author}! \n \n Motivo: {reason}" if lang == "pt" else f"{member} was kicked out by {ctx.author}! \n \n Reason: {reason}"
            await ctx.send(msg)

    @commands.command(aliases=["timeout", "castigo", "disciplinar"])
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, *, time: str = "60m"):
        """
            Mutes a member!

            Syntax: !mute @user-to-mute <time>
            If no time is specified, it defaults to 60 minutes.

            Examples:
            !mute @user 10 s | !mute @user 5m | !mute @user 2h | !mute @user 1d
        """

        print("User typed !mute") # LOG

        lang = get_user_lang(ctx.author.id)

        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        unit = time[-1]
        number = time[:-1]

        if unit not in units or not number.isdigit():
            msg = "Formato invalido! \n \n Síntaxe: !mute @user 60s \n \n Unidades Suportadas: \n \n s Segundos | m Minutos | h Horas | d Dias" if lang == "pt" else "Invalid Format! \n \n Syntax: !mute @user 60s \n \n Units Supported: \n \n s Seconds | m Minutes | h Hours | d Days"
            await ctx.send(msg)
            return

        seconds = int(number) * units[unit]
        duration = datetime.timedelta(seconds=seconds)

        await  member.timeout(duration)

        msg = f"{member.name} foi pro cantinho da disciplina por {time}!" if lang == "pt" else f"{member.name} was sent to timeout for {time}!"
        await ctx.send(msg)

    @commands.command(aliases=["deletar"])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, ammount: int = 100):
        """
            Deletes the n most recent messages

            Syntax: !purge <ammount>
            If no ammount is defined, defaults to 100.
        """
        print(f"User typed !purge {ammoun}") # LOG
        await ctx.channel.purge(limit=ammount + 1) # +1 needed to clear the ammount + the author message

async def setup(bot):
    await bot.add_cog(Admin(bot))
