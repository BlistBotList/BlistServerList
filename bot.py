import argparse
import datetime
import os
import traceback
from typing import Union

import aiohttp
import asyncpg
import discord
from discord.ext import commands

import config
from cogs.help import CustomHelpCommand
from utils.constants import MAIN_GUILD_ID

parser = argparse.ArgumentParser()
parser.add_argument(
    "-d",
    "--development",
    help="Run the bot in the development state",
    action="store_true",
)
args = parser.parse_args()


class Blist(commands.Bot):
    pool: asyncpg.Pool
    user: discord.ClientUser

    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(
                *["bs?", "Bs?", "bS?", "BS?"]
                if args.development
                else ["bs!", "Bs!", "bS!", "BS!"]
            ),
            case_insensitive=True,
            max_messages=500,
            reconnect=True,
            help_command=CustomHelpCommand(command_attrs={"hidden": True}),
            intents=discord.Intents(
                members=True,
                emojis=True,
                messages=True,
                guilds=True,
                message_content=True,
            ),
        )

    @property
    def main_guild(self) -> Union[discord.Guild, discord.Object]:
        return self.get_guild(MAIN_GUILD_ID) or discord.Object(MAIN_GUILD_ID)

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        print("---------------------")
        print(f"{self.user} is ready")
        print("---------------------")
        self.uptime = datetime.datetime.utcnow().strftime("%c")

        try:
            self.pool = await asyncpg.create_pool(config.db_url)  # type: ignore
        except Exception as error:
            print("There was a problem connecting to the database")
            print(f"\n{error}")

        for file in os.listdir("cogs"):
            if file.endswith(".py") and not file.startswith("_"):
                try:
                    await self.load_extension(f"cogs.{file[:-3]}")
                except commands.ExtensionFailed as e:
                    print(f"Failed to load {file}")
                    traceback.print_exception(e.__class__, e, e.__traceback__)
                else:
                    print(f"Successfully loaded {file}!")

        try:
            await self.load_extension("jishaku")
        except commands.ExtensionFailed as e:
            print("Failed to load jishaku")
            traceback.print_exception(e.__class__, e, e.__traceback__)
        else:
            print(f"Successfully loaded jishaku!")

    async def close(self):
        if hasattr(self, "pool"):
            await self.pool.close()
        if hasattr(self, "session"):
            await self.session.close()
        await super().close()

    def run(self):
        return super().run(
            config.bot_token_dev if args.development else config.bot_token
        )


if __name__ == "__main__":
    Blist().run()
