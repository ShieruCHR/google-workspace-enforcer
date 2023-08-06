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
    if not settings.validate_settings(interaction.client).is_valid:
        message_prefix = ""
        await interaction.response.send_message(
            f"一部の設定が間違っているため、認証を開始できません。\nサーバーの管理者にお問い合わせください。\n\nもしあなたがサーバーの管理者なら、`/settings`を実行して設定を確認してください。",
            ephemeral=True,
        )
        return
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
    "panel",
    help="認証用のパネルを設置します。チャンネルが指定されればそこへ、指定されなければ実行したチャンネルに送信されます。",
)
@discord.app_commands.default_permissions(manage_messages=True)
@discord.app_commands.guild_only()
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
@discord.app_commands.guild_only()
async def verify(ctx: Context):
    await start_verification(ctx.interaction)


@bot.hybrid_command("settings", help="設定を確認します。")
@discord.app_commands.default_permissions(manage_guild=True)
@discord.app_commands.guild_only()
async def validate_settings(ctx: Context):
    embed = discord.Embed(title="Settings Validator")
    embed.set_footer(
        text="この機能は簡易チェックです。一度認証を試してみることをおすすめします！",
        icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None,
    )
    settings = get_settings(next(get_session()), ctx.guild.id)
    result = settings.validate_settings(ctx.bot)

    def bool_to_str(b: bool) -> str:
        return ":white_check_mark: 利用可能" if b else ":no_entry_sign: 利用不可"

    unavailable_role_reasons = "\n".join(
        [f"- {tag.value}" for tag in result.verified_role_reasons]
    )
    unavailable_channel_reasons = "\n".join(
        [f"- {tag.value}" for tag in result.log_channel_reasons]
    )
    if result:
        embed.description = f"""
        __**役職の確認**__
        「認証済み」の役職: {result.verified_role.mention if result.verified_role else 'Invalid'}
        役職の利用可能ステータス: **{bool_to_str(result.verified_role_grantable)}**
        理由:
          {unavailable_role_reasons}

        -------

        __**ログチャンネルの確認**__
        認証ログチャンネル: {result.log_channel.mention if result.log_channel else 'Invalid'}
        チャンネルの利用可能ステータス: **{bool_to_str(result.log_channel_sendable)}**
        理由:
          {unavailable_channel_reasons}

        -------

        __**ドメイン**__
        認証可能なドメイン: {settings.friendly_allowed_domains}
        """
    else:
        embed.description = "Failed to validate settings. Please try again later."
    await ctx.send(
        "認証は利用可能です。正しく構成されています！"
        if result.is_valid
        else "設定の一部が間違っているため、認証できません。詳細は以下を確認してください:",
        embed=embed,
    )
