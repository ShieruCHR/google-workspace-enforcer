from logging import getLogger
import os
from uuid import uuid4
import discord
from discord.ext import commands
from discord import Intents
from discord.ext.commands import Context
from database import get_session
from settings_utils import get_settings

from views import RoleView, VerifyView
import logging

processing_states = {}


intent = Intents.default()
intent.members = True
bot = commands.Bot(command_prefix="!", intents=intent)
bot.remove_command("help")
logger = getLogger("discord")
logger.setLevel(logging.WARNING)
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)


async def start_verification(interaction: discord.Interaction):
    state = str(uuid4())
    settings = get_settings(next(get_session()), interaction.guild.id)
    processing_states[state] = {
        "guild_name": interaction.guild.name,
        "domain": settings.allowed_domains,
        "guild_id": interaction.guild.id,
    }
    url = os.getenv("HOST") + "/" + state
    message_prefix = (
        "認証を開始します！以下のURLにアクセスして、あなたがGoogle Workspaceのアカウントに関連付けられている人物かを認証してください。"
    )
    if settings.allowed_domains:
        await interaction.response.send_message(
            f"{message_prefix}\n**Google アカウントの認証は{settings.friendly_allowed_domains}{'のいずれか' if len(settings.allowed_domains) > 1 else ''}のアカウントで行う必要があります。**\n{url}",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            f"{message_prefix}\n{url}",
            ephemeral=True,
        )


bot.add_view(VerifyView(start_verification))
bot.add_view(RoleView())


@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot is ready!")


@bot.hybrid_command(
    "panel", help="認証用のパネルを設置します。チャンネルが指定されればそこへ、指定されなければ実行したチャンネルに送信されます。"
)
@commands.has_guild_permissions(manage_guild=True)
async def create_panel(ctx: Context, channel: discord.TextChannel = None):
    settings = get_settings(next(get_session()), ctx.guild.id)
    embed = discord.Embed(title="Google Workspaceの認証")
    embed.description = f"このサーバーに参加するには、あなたが{settings.friendly_allowed_domains}{'のいずれか' if len(settings.allowed_domains) > 1 else ''}に所属するメンバーかを認証する必要があります。\n下のボタンを押すか、`/verify`を実行して認証を開始してください！"
    if channel is None:
        channel = ctx.channel
    await channel.send(view=VerifyView(start_verification), embed=embed)
    await ctx.interaction.response.send_message(
        f"Success!", ephemeral=True, delete_after=5
    )


@bot.hybrid_command("verify", help="認証用のURLを発行し、認証を開始します。")
async def verify(ctx: Context):
    await start_verification(ctx.interaction)
