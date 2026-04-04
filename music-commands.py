class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello from a Cog!")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        pass
async def setup(bot):
    await bot.add_cog(Music(bot))