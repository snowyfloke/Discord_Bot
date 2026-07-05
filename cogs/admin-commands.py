import discord
import datetime
from discord.ext import commands
from discord import app_commands
from lang import get_user_lang, get_msg


class Admin(commands.Cog):
    """
    Server Management Section
    Most commands require admin permissions!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(
        member="Member to be banned, cannot be an admin",
        reason="Reason to ban, defaults to None",
    )
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """
        Bans a member!

        Syntax: !ban @user-to-ban <reason>
        If no reason is defined, it defaults to none.
        """
        print("User typed !ban")  # LOG
        lang = get_user_lang(ctx.author.id)
        if member.guild_permissions.administrator:
            msg = get_msg(lang, "ban_admin")
            await ctx.send(msg)
            return

        else:
            await member.ban(reason=reason)
            msg = get_msg(lang, "ban_member").format(
                member_banned=member, author=ctx.author, reason_to_ban=reason
            )
            await ctx.send(msg)

    @commands.hybrid_command(aliases=["expulsar"])
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(
        member="Member to be kicked out, cannot be an admin",
        reason="Reason to kick, defaults to None",
    )
    async def kick(self, ctx, member: discord.Member, reason=None):
        """
        Kicks a member!

        Syntax: !kick @user-to-kick <reason>
        If no reason is defined, it defaults to none.
        """
        print("User typed !kick")  # LOG
        lang = get_user_lang(ctx.author.id)
        if member.guild_permissions.administrator:
            msg = get_msg(lang, "kick_admin")
            await ctx.send(msg)
            return
        else:
            await member.kick(reason=reason)
            msg = get_msg(lang, "kick_member").format(
                member_kicked=member, author=ctx.author, reason_to_kick=reason
            )
            await ctx.send(msg)

    @commands.hybrid_command(aliases=["to", "castigo", "disciplinar"])
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(
        member="Member to be timeouted",
        time="Ammount to timeout, s Seconds, m Minutes, h Hours, d Days, defaults to 60m",
    )
    async def timeout(self, ctx, member: discord.Member, *, time: str = "60m"):
        """
        Timeouts a member!

        Syntax: !timeout @user-to-mute <time>
        If no time is specified, it defaults to 60 minutes.

        Examples:
        !timeout @user 10s | !timeout @user 5m | !timeout @user 2h | !timeout @user 1d
        """

        print("User typed !mute")  # LOG

        lang = get_user_lang(ctx.author.id)

        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        unit = time[-1]
        number = time[:-1]

        if unit not in units or not number.isdigit():
            syntax_msg = get_msg(lang, "wrong_syntax").format(syntax="!timeout <@user> 60s")
            units_msg = get_msg(lang, "supported_units").format(units="s, m, h, d")
            await ctx.send(f"{syntax_msg}\n\n{units_msg}")
            return

        seconds = int(number) * units[unit]
        duration = datetime.timedelta(seconds=seconds)

        await member.timeout(duration)

        msg = get_msg(lang, "timeout").format(member_timeouted=member.name, time=time)
        await ctx.send(msg)

    @commands.hybrid_command(aliases=["deletar"])
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(ammount="Number of messages to purge, defaults to 100")
    async def purge(self, ctx, ammount: int = 100):
        """
        Deletes the n most recent messages

        Syntax: !purge <ammount>
        If no ammount is defined, defaults to 100.
        """
        print(f"User typed !purge {ammount}")  # LOG
        await ctx.channel.purge(
            limit=ammount + 1
        )  # +1 needed to clear the ammount + the author message

    @commands.hybrid_command(aliases=["foto-de-perfil", "avatar"])
    @app_commands.describe(member="Member to grab the pfp, defaults to you!")
    async def pfp(self, ctx, member: discord.Member = None):
        """
        Sends the pfp of a member as a .jpeg or .gif!

        Syntax: !pfp @member
        """
        if member == None:
            member = ctx.author

        icon_url = member.display_avatar.url
        avatarEmbed = discord.Embed(title=f"{member.name}'s Avatar", color=0xFFA500)

        avatarEmbed.set_image(url=f"{icon_url}")

        avatarEmbed.timestamp = ctx.message.created_at

        await ctx.send(embed=avatarEmbed)


async def setup(bot):
    await bot.add_cog(Admin(bot))
