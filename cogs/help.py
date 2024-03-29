from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from jishaku.help_command import MinimalEmbedPaginatorHelp
from jishaku.paginators import PaginatorEmbedInterface

if TYPE_CHECKING:
    from bot import Blist


class CustomPaginatorEmbedInterface(PaginatorEmbedInterface):
    bot: Blist

    @property
    def send_kwargs(self) -> dict:
        display_page = self.display_page
        self._embed.title = self.bot.user.name
        self._embed.description = self.pages[display_page]
        self._embed.color = discord.Colour.blurple()
        page_string = f"Page {display_page + 1}/{self.page_count}"
        if self.owner:
            self._embed.set_footer(
                text=f"{self.owner.name} | {page_string}",
                icon_url=self.owner.display_avatar.url,
            )
        else:
            self._embed.set_footer(text=page_string)

        return {"embed": self._embed}


class CustomHelpCommand(MinimalEmbedPaginatorHelp):
    async def send_pages(self):
        destination = self.get_destination()
        interface = CustomPaginatorEmbedInterface(
            self.context.bot, self.paginator, owner=self.context.author
        )
        await interface.send_to(destination)

    def add_bot_commands_formatting(self, _commands, heading):
        if commands:
            # U+2022 Middle Dot
            joined = ", ".join(f"`{c.name}`" for c in _commands)
            self.paginator.add_line(f"> **{heading}**")
            self.paginator.add_line(f"{joined}\n")

    def get_opening_note(self):
        """Returns help command's opening note. This is mainly useful to override for i18n purposes.
        The default implementation returns ::
            Use `{prefix}{command_name} [command]` for more info on a command.
            You can also use `{prefix}{command_name} [category]` for more info on a category.
        """
        return f"To get help on a specific command or category do `{self.context.clean_prefix}help [command or category name]`"


class Help(commands.Cog):
    def __init__(self, bot: Blist) -> None:
        self.bot: Blist = bot

    def cog_load(self) -> None:
        self.bot._old_help_command = self.bot.help_command  # type: ignore
        self.bot.help_command = MinimalEmbedPaginatorHelp(
            command_attrs={"hidden": True}
        )

    def cog_unload(self) -> None:
        self.bot.help_command = self._old_help_command  # type: ignore


async def setup(bot: Blist) -> None:
    await bot.add_cog(Help(bot))
