import os

from dotenv import load_dotenv
from sqlmodel import Session, select

from models import GuildSettings

load_dotenv()
allowed_domains = os.getenv("DOMAINS", "").split(",")
public_bot = bool(int(os.getenv("PUBLIC_BOT_FEATURES", "0")))


def is_allowed(session: Session, domain: str, guild_id: int):
    settings = get_settings(session, guild_id)
    if len(settings.allowed_domains) == 0:
        return True
    return domain in settings.allowed_domains


def friendly_allowed_domains(session: Session, guild_id: int):
    settings = get_settings(session, guild_id)
    return ", ".join(settings.allowed_domains)


def get_settings(session: Session, guild_id: int):
    if public_bot:
        return session.exec(
            select(GuildSettings).where(GuildSettings.guild_id == str(guild_id))
        ).first()
    else:
        return GuildSettings(
            guild_id=guild_id,
            allowed_domains_str=os.getenv("DOMAINS", ""),
            verified_role_id=os.getenv("VERIFIED_ROLE_ID"),
            verification_log_channel_id=os.getenv("VERIFICATION_LOG_CHANNEL_ID"),
        )
