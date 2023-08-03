import os
import re
import discord
from discord.ext import commands
from sqlmodel import Session, select
from database import get_session

from models import GuildSettings
from settings_utils import get_settings


class PublicBotCog(commands.Cog):
    bot: commands.Bot

    def __init__(self, bot) -> None:
        self.bot = bot

    def create_settings(self, session: Session, guild_id: int):
        settings = GuildSettings(
            allowed_domains_str="",
            guild_id=guild_id,
            verified_role_id="",
            verification_log_channel_id="",
        )
        session.add(settings)
        return settings

    def is_domain_available(self, domain: str):
        return bool(
            re.match(
                r"^(?!:\/\/)(?!.*\.\.)[a-zA-Z0-9-]{1,63}\.[a-zA-Z]{2,63}$",
                domain,
            )
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        # Create settings for guild
        session = next(get_session())
        self.create_settings(session, guild.id)
        session.commit()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        # Delete settings for guild
        session = next(get_session())
        session.delete(get_settings(session, guild.id))
        session.commit()

    @commands.hybrid_command("create")
    @commands.is_owner()
    async def create_settings_command(self, ctx: commands.Context):
        session = next(get_session())
        self.create_settings(session, ctx.guild.id)
        session.commit()

    @commands.hybrid_command("role")
    async def set_verification_role(self, ctx: commands.Context, role: discord.Role):
        session = next(get_session())
        settings = get_settings(session, ctx.guild.id)
        settings.verified_role_id = role.id
        session.commit()
        await ctx.send(
            f"「認証済み」ロールを以下に設定しました: {role.mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.hybrid_command("channel")
    async def set_verification_log_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        session = next(get_session())
        settings = get_settings(session, ctx.guild.id)
        settings.verification_log_channel_id = channel.id
        session.commit()
        await ctx.send(f"認証ログチャンネルを以下に設定しました: {channel.mention}")

    @commands.hybrid_group("domains")
    @commands.has_guild_permissions(manage_guild=True)
    async def domains_group(self, ctx: commands.Context):
        pass

    @domains_group.command("add")
    async def domains_add_command(self, ctx: commands.Context, domain: str):
        if not self.is_domain_available(domain):
            await ctx.send(f"このドメインは使用できません。")
            return
        session = next(get_session())
        settings = get_settings(session, ctx.guild.id)
        domain_limit = int(os.getenv("DOMAIN_LIMITS", 3))
        if domain_limit <= len(settings.allowed_domains):
            await ctx.send(
                f"公開Botでは、認証できるドメインの数は{domain_limit}個までに制限されています。\n既にあるドメインを削除するか、Botの管理者に直接問い合わせてください: {os.getenv('SUPPORT_LINK')}"
            )
            return
        if domain in settings.allowed_domains:
            await ctx.send(f"既にこのドメインは追加されています: `{domain}`")
            return
        settings.add_allowed_domain(domain)
        session.commit()
        await ctx.send(f"認証できるドメインに以下を追加しました: `{domain}`")

    @domains_group.command("remove")
    async def domains_remove_command(self, ctx: commands.Context, domain: str):
        if not self.is_domain_available(domain):
            await ctx.send(f"このドメインは使用できません。")
            return
        session = next(get_session())
        settings = get_settings(session, ctx.guild.id)
        if domain not in settings.allowed_domains:
            await ctx.send(f"以下は認証できるドメインではありません: `{domain}`")
            return
        settings.remove_allowed_domain(domain)
        session.commit()
        await ctx.send(f"認証できるドメインから以下を削除しました: `{domain}`")

    @domains_group.command("clear")
    async def domains_clear_command(self, ctx: commands.Context):
        session = next(get_session())
        settings = get_settings(session, ctx.guild.id)
        settings.allowed_domains_str = ""
        session.commit()
        await ctx.send(f"認証できるドメインをクリアしました。")

    @domains_group.command("list")
    async def domains_list(self, ctx: commands.Context):
        session = next(get_session())
        settings = get_settings(session, ctx.guild.id)
        embed = discord.Embed(
            title=f"認証できるドメイン一覧 ({len(settings.allowed_domains)} / {os.getenv('DOMAIN_LIMITS')})"
        )
        embed.description = "\n".join(settings.allowed_domains)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PublicBotCog(bot))
    print("Public bot extension has been loaded.")
