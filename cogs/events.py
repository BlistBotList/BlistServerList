from __future__ import annotations

import datetime
import random
import sys
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands, tasks

import config

if TYPE_CHECKING:
    from bot import Blist


class Events(commands.Cog):
    def __init__(self, bot: Blist) -> None:
        self.bot: Blist = bot

    def cog_load(self) -> None:
        self.old_on_error = self.bot.on_error
        self.bot.on_error = self.new_on_error
        self.change_status.start()

    def cog_unload(self) -> None:
        self.bot.on_error = self.old_on_error

    @tasks.loop(hours=1)
    async def change_status(self) -> None:
        unpublished = await self.bot.pool.fetchval(
            "SELECT COUNT(*) FROM main_site_server WHERE published = False"
        )
        published = await self.bot.pool.fetchval(
            "SELECT COUNT(*) FROM main_site_server WHERE published = True"
        )
        options = [
            f"with {published} published servers",
            f"with {unpublished} un-published servers",
            f"with {str(len(set(self.bot.get_all_members())))} total users",
        ]
        await self.bot.change_presence(
            activity=discord.Game(name=random.choice(options))
        )

    @property
    def error_webhook(self) -> discord.Webhook:
        token = config.error_webhook_token
        web_id = config.error_webhook_id
        hook = discord.Webhook.partial(id=web_id, token=token, session=self.bot.session)
        return hook

    async def new_on_error(self, event, *args: Any, **kwargs: Any) -> None:
        error = sys.exc_info()
        if not error[1]:
            return
        em = discord.Embed(
            title="Server Bot Error:",
            description=f"**Event**: {event}\n```py\n{error[1]}\n\n{error}```",
            color=discord.Color.blurple(),
        )
        await self.error_webhook.send(embed=em)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context[Blist], error: commands.CommandError
    ) -> Any:
        ignored = (
            commands.CommandNotFound,
            commands.DisabledCommand,
            commands.TooManyArguments,
        )
        send_embed = (
            commands.MissingPermissions,
            discord.HTTPException,
            commands.NotOwner,
            commands.CheckFailure,
            commands.MissingRequiredArgument,
            commands.BadArgument,
            commands.BadUnionArgument,
        )

        errors = {
            commands.MissingPermissions: "You do not have permissions to run this command.",
            discord.HTTPException: "There was an error connecting to Discord. Please try again.",
            commands.CommandInvokeError: "There was an issue running the command.",
            commands.NotOwner: "You are not the owner.",
            commands.CheckFailure: "This command cannot be used in this guild!",
            commands.MissingRole: "You're missing the **{}** role",
            commands.MissingRequiredArgument: "`{}` is a required argument!",
        }

        if isinstance(error, ignored):
            return

        if isinstance(error, send_embed):
            if isinstance(error, commands.MissingRequiredArgument):
                err = errors.get(error.__class__).format(  # type: ignore
                    str(error.param).partition(":")[0]
                )
            elif isinstance(error, commands.MissingRole):
                role = ctx.guild.get_role(error.missing_role)  # type: ignore
                err = errors.get(error.__class__).format(role.mention)  # type: ignore
            else:
                efd = errors.get(error.__class__)  # type: ignore
                err = str(efd)
                if not efd:
                    err = str(error)

            em = discord.Embed(description=str(err), color=discord.Color.red())
            try:
                await ctx.send(embed=em)
                return
            except discord.Forbidden:
                pass

        # when error is not handled above
        em = discord.Embed(
            title="Server Bot Error:",
            description=f"```py\n{error}\n```",
            color=discord.Color.blurple(),
        )
        await ctx.send(
            embed=discord.Embed(
                description=f"Something went wrong... {type(error).__name__}",
                color=discord.Color.red(),
            )
        )
        await self.error_webhook.send(embed=em)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        db_check = await self.bot.pool.fetch(
            "SELECT * FROM main_site_user WHERE id = $1", guild.owner_id
        )
        try:
            premium = db_check[0]["premium"]
        except IndexError:
            premium = False

        avatar_hash = (
            guild.icon
            or "https://blist.xyz/main_site/staticfiles/main/assets/question-mark.png"
        )

        managers = " ".join(
            [
                str(x.id)
                for x in guild.members
                if x.guild_permissions.manage_guild and not x.bot
            ]
        )
        await self.bot.pool.execute(
            "INSERT INTO main_site_server (name, id, main_owner, website, short_description, invite_url, tags, monthly_votes, total_votes, vanity_url, member_count, added, webhook_url, joins, page_views, donate_url, card_background, premium, icon_hash, published, archived, managers) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)",
            guild.name,
            guild.id,
            guild.owner_id,
            "",
            "",
            "",
            [""],
            0,
            0,
            "",
            len(guild.members),
            datetime.datetime.utcnow(),
            "",
            0,
            0,
            "",
            "",
            premium,
            avatar_hash,
            False,
            False,
            managers,
        )
        logs = self.bot.main_guild.get_channel(793584504291065857)  # type: ignore
        embed = discord.Embed(
            title="New Server Joined!",
            color=discord.Color.blurple(),
            description=f"""
>>> **Name:** {guild.name}
**Member Count:** {len(guild.members)}
**Owner:** {guild.owner} ({guild.owner_id})
""",
        )
        embed.set_thumbnail(url=str(guild.icon) if guild.icon else None)
        await logs.send(embed=embed)  # type: ignore

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        unique_id = await self.bot.pool.fetchval(
            "SELECT unique_id FROM main_site_server WHERE id = $1", guild.id
        )
        await self.bot.pool.execute(
            "DELETE FROM main_site_servervote WHERE server_id = $1", unique_id
        )
        await self.bot.pool.execute(
            "DELETE FROM main_site_serverauditlogaction WHERE server_id = $1", unique_id
        )
        await self.bot.pool.execute(
            "DELETE FROM main_site_server WHERE id = $1", guild.id
        )
        logs = self.bot.main_guild.get_channel(793584504291065857)  # type: ignore
        embed = discord.Embed(
            title="Server Left!",
            color=discord.Color.blurple(),
            description=f"""
>>> **Name:** {guild.name}
**Member Count:** {len(guild.members)}
**Owner:** {guild.owner} ({guild.owner_id})
""",
        )
        embed.set_thumbnail(url=str(guild.icon) if guild.icon else None)
        await logs.send(embed=embed)  # type: ignore


async def setup(bot: Blist) -> None:
    await bot.add_cog(Events(bot))
