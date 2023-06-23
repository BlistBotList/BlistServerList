from __future__ import annotations

import asyncio
import os
import re
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from bot import Blist


class General(commands.Cog):
    def __init__(self, bot: Blist) -> None:
        self.bot: Blist = bot

    @commands.command()
    async def stats(self, ctx: commands.Context[Blist]):
        unpublished = await self.bot.pool.fetchval(
            "SELECT COUNT(*) FROM main_site_server WHERE published = False"
        )
        published = await self.bot.pool.fetchval(
            "SELECT COUNT(*) FROM main_site_server WHERE published = True"
        )
        embed = discord.Embed(
            title="Blist Servers Stats",
            color=discord.Color.blurple(),
            description=f"""
>>> ``Published Servers:`` {published}
``Un-Published Servers:`` {unpublished}""",
        )
        if ctx.guild and ctx.guild.icon:
            embed.set_thumbnail(url=str(ctx.guild.icon.url))
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx: commands.Context[Blist]):
        await ctx.send(discord.utils.oauth_url(self.bot.user.id))

    @commands.command()
    @commands.is_owner()
    async def restart(self, ctx: commands.Context[Blist]):
        await ctx.send("Restarting")
        os.system("systemctl restart blists")

    @commands.command()
    @commands.is_owner()
    async def update(self, ctx: commands.Context[Blist]):
        """Pulls from a git remote and reloads modified cogs"""
        async with ctx.typing():
            process = await asyncio.create_subprocess_exec(
                "git",
                "pull",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                com = await asyncio.wait_for(process.communicate(), timeout=5)
                com = com[0].decode() + "\n" + com[1].decode()
            except asyncio.TimeoutError:
                await ctx.send("The process timed out.")
                return

            reg = r"\S+(\.py)"
            reg = re.compile(reg)
            found = [
                match.group()[:-3].replace("/", ".") for match in reg.finditer(com)
            ]

            if found:
                updated = []
                for file in found:
                    try:
                        await self.bot.reload_extension(file)
                        updated.append(file)
                    except (commands.ExtensionNotLoaded, commands.ExtensionNotFound):
                        continue
                    except Exception as e:
                        embed = discord.Embed(
                            title=f"There was an issue pulling from GitHub",
                            description=f"\n```{e}```\n",
                            color=discord.Color.red(),
                        )
                        await ctx.send(embed=embed)
                        return

                if not updated:
                    embed = discord.Embed(
                        title=f"No cogs were updated.", color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title=f"Updated cogs: "
                        + ", ".join([f"`{text}`" for text in updated]),
                        color=discord.Color.blurple(),
                    )
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"No cogs were updated.", color=discord.Color.red()
                )
                await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))
