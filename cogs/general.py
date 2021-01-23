from discord.ext import commands
import discord
import os
import asyncio

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


    @commands.is_owner()
    @commands.command()
    async def update(self, ctx):
        """Pulls from a git remote and reloads modified cogs"""
        await ctx.channel.trigger_typing()
        process = await asyncio.create_subprocess_exec(
            "git", "pull",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            com = await asyncio.wait_for(process.communicate(), timeout=5)
            com = com[0].decode() + "\n" + com[1].decode()
        except asyncio.TimeoutError:
            await ctx.send("The process timed out.")

        reg = r"\S+(\.py)"
        reg = re.compile(reg)
        found = [match.group()[:-3].replace("/", ".")
                 for match in reg.finditer(com)]

        if found:
            updated = []
            for file in found:
                try:
                    self.bot.reload_extension(file)
                    updated.append(file)
                except (commands.ExtensionNotLoaded, commands.ExtensionNotFound):
                    continue
                except Exception as e:
                    embed = discord.Embed(title=f"There was an issue pulling from GitHub",
                                          description=f"\n```{e}```\n", color=discord.Color.red())
                    await ctx.send(embed=embed)
                    return

            if not updated:
                embed = discord.Embed(
                    title=f"No cogs were updated.", color=discord.Color.red())
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"Updated cogs: " +
                    ", ".join([f"`{text}`" for text in updated]),
                    color=discord.Color.blurple())
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"No cogs were updated.", color=discord.Color.red())
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(General(bot))