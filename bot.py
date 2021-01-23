import argparse
import datetime
import os

import aiohttp
import asyncpg
import discord
from discord.ext import commands

import config
from cogs.help import CustomHelpCommand

extensions = ["jishaku"]

for f in os.listdir("cogs"):
    if f.endswith(".py") and f"cogs.{f[:-3]}" not in extensions:
        extensions.append("cogs." + f[:-3])

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--development",
                    help="Run the bot in the development state", action="store_true")
args = parser.parse_args()


class Blist(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=["bs?", "Bs?", "bS?", "BS?"] if args.development else [
                "bs!", "Bs!", "bS!", "BS!"],
            case_insensitive=True,
            max_messages=500,
            reconnect=True,
            help_command=CustomHelpCommand(command_attrs={'hidden': True}),
            intents=discord.Intents(
                members=True, emojis=True, messages=True, guilds=True)
        )

    async def on_ready(self):
        self.session = aiohttp.ClientSession()
        print("---------------------")
        print(f"{self.user} is ready")
        print("---------------------")
        self.uptime = datetime.datetime.utcnow().strftime("%c")

    async def on_connect(self):
        self.main_guild = self.get_guild(716445624517656727)
        if not hasattr(self, "pool"):
            try:
                self.pool = await asyncpg.create_pool(config.db_url)
            except Exception as error:
                print("There was a problem connecting to the database")
                print(f"\n{error}")

        for extension in extensions:
            self.load_extension(extension)

    async def start(self):
        await self.login(config.bot_token_dev if args.development else config.bot_token)
        try:
            await self.connect()
        except KeyboardInterrupt:
            await self.stop()

    async def stop(self):
        await self.pool.close()
        await super().logout()

    def run(self):
        loop = self.loop
        try:
            loop.run_until_complete(self.start())
        except KeyboardInterrupt:
            loop.run_until_complete(self.stop())


if __name__ == "__main__":
    Blist().run()