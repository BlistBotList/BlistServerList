from discord.ext import commands
import discord
import os

class General(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def stats(self, ctx):
        unpublished = await self.bot.pool.fetchval("SELECT COUNT(*) FROM main_site_server WHERE published = False")
        published = await self.bot.pool.fetchval("SELECT COUNT(*) FROM main_site_server WHERE published = True")
        embed = discord.Embed(title="Blist Servers Stats", color=discord.Color.blurple(), description=f"""
>>> ``Published Servers:`` {published}
``Un-Published Servers:`` {unpublished}""")
        embed.set_thumbnail(url=str(ctx.guild.icon_url))
        await ctx.send(embed=embed)


    @commands.command()
    async def invite(self, ctx):
        await ctx.send(discord.utils.oauth_url(self.bot.user.id))


    @commands.is_owner()
    @commands.command()
    async def restart(self, ctx):
        await ctx.send("Restarting")
        os.system("systemctl restart blists")


def setup(bot):
    bot.add_cog(General(bot))