import discord
from discord.ext import commands


class PublicBotCog(commands.Cog):
    bot: commands.Bot

    def __init__(self, bot) -> None:
        self.bot = bot


def setup(bot: commands.Bot) -> None:
    bot.add_cog(PublicBotCog(bot))
    print("PublicBotCog loaded")
