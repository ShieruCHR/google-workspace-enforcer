import os
import discord
from discord.ext import commands
from sqlmodel import Session, select
from database import get_session

from models import GuildSettings


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

    def get_settings(self, session: Session, guild_id: int) -> GuildSettings:
        return session.exec(
            select(GuildSettings).where(GuildSettings.guild_id == guild_id)
        ).first()

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
        session.delete(self.get_settings(session, guild.id))
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
        settings = self.get_settings(session, ctx.guild.id)
        settings.verified_role_id = role.id
        session.commit()
        await ctx.send(f"Verification role set to {role.name}")

    @commands.hybrid_command("channel")
    async def set_verification_log_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        session = next(get_session())
        settings = self.get_settings(session, ctx.guild.id)
        settings.verification_log_channel_id = channel.id
        session.commit()
        await ctx.send(f"Verification log channel set to {channel.mention}")

    @commands.hybrid_group("domains")
    async def domains_group(self, ctx: commands.Context):
        pass

    @domains_group.command("add")
    async def domains_add_command(self, ctx: commands.Context, domain: str):
        session = next(get_session())
        settings = self.get_settings(session, ctx.guild.id)
        if int(os.getenv("DOMAIN_LIMITS", 3)) < len(settings.allowed_domains):
            await ctx.send(f"Limit exceeded. Remove some domains first.")
            return
        settings.add_allowed_domain(domain)
        session.commit()
        await ctx.send(f"Added domain {domain}")

    @domains_group.command("remove")
    async def domains_remove_command(self, ctx: commands.Context, domain: str):
        session = next(get_session())
        settings = self.get_settings(session, ctx.guild.id)
        settings.remove_allowed_domain(domain)
        session.commit()
        await ctx.send(f"Removed domain {domain}")

    @domains_group.command("list")
    async def domains_list(self, ctx: commands.Context):
        session = next(get_session())
        settings = self.get_settings(session, ctx.guild.id)
        embed = discord.Embed(title="Allowed domains")
        embed.description = "\n".join(settings.allowed_domains)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PublicBotCog(bot))
    print("PublicBotCog loaded")
