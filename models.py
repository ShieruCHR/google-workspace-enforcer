from enum import Enum
import discord
from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel


class GuildSettings(SQLModel, table=True):
    guild_id: str = Field(default=None, primary_key=True)
    allowed_domains_str: str = Field(
        sa_column=Column("allowed_domains", String, default=None)
    )
    verified_role_id: str = Field(default=None)
    verification_log_channel_id: str = Field(default=None)

    @property
    def allowed_domains(self):
        if self.allowed_domains_str:
            return self.allowed_domains_str.split(",")
        else:
            return []

    def set_allowed_domains(self, *domains):
        self.allowed_domains_str = ",".join(set(domains))

    def add_allowed_domain(self, domain):
        self.set_allowed_domains(*((*self.allowed_domains, domain)))

    def remove_allowed_domain(self, domain):
        self.set_allowed_domains(*[d for d in self.allowed_domains if d != domain])

    @property
    def friendly_allowed_domains(self):
        return ", ".join(self.allowed_domains)

    def is_allowed(self, domain):
        return domain in self.allowed_domains if self.allowed_domains else True

    def validate_settings(self, bot: discord.Client):
        result = SettingsValidationResult()
        log_channel = bot.get_channel(int(self.verification_log_channel_id))
        verified_role = bot.get_guild(int(self.guild_id)).get_role(
            int(self.verified_role_id)
        )
        guild = bot.get_guild(int(self.guild_id))

        # Log channel availability check
        ## Is Log channel exists?
        if log_channel is None:
            log_channel_availability = False
            result.log_channel_reasons.append(SettingsValidationTag.NOT_FOUND)
        else:
            ## Permission check (send messages)
            if log_channel.permissions_for(log_channel.guild.me).send_messages:
                log_channel_availability = True
                result.log_channel_reasons.append(SettingsValidationTag.OK)
            else:
                log_channel_availability = False
                result.log_channel_reasons.append(SettingsValidationTag.NO_PERMISSION)

        # Role availability check

        ## Is Role exists?
        if verified_role is None:
            role_availability = False
            result.verified_role_reasons.append(SettingsValidationTag.NOT_FOUND)
        else:
            ## Permission check (manage_roles)
            if not guild.me.guild_permissions.manage_roles:
                role_availability = False
                result.verified_role_reasons.append(SettingsValidationTag.NO_PERMISSION)
            ## Is role managed?
            if verified_role.managed:
                role_availability = False
                result.verified_role_reasons.append(SettingsValidationTag.ROLE_MANAGED)
            ## Is role higher than bot's top role?
            if (
                verified_role.position >= guild.me.top_role.position
                and guild.owner != bot
            ):
                role_availability = False
                result.verified_role_reasons.append(SettingsValidationTag.ROLE_HIGHER)

            if len(result.verified_role_reasons) == 0:
                role_availability = True
                result.verified_role_reasons.append(SettingsValidationTag.OK)

        result.domains = self.allowed_domains
        result.log_channel = log_channel
        result.log_channel_sendable = log_channel_availability
        result.verified_role = verified_role
        result.verified_role_grantable = role_availability
        return result


class SettingsValidationTag(Enum):
    NOT_FOUND = "Not Found: 見つからないか、削除されています。"
    NO_PERMISSION = "No Permission: 権限がありません。"
    ROLE_MANAGED = "Managed Role: Discordによる管理ロールは設定できません。"
    ROLE_HIGHER = "Higher Role: Botよりも上位のロールです。"

    OK = ":white_check_mark: OK: 正しく構成されています！"


class SettingsValidationResult:
    log_channel: discord.TextChannel
    log_channel_sendable: bool
    log_channel_reasons: list[SettingsValidationTag]
    verified_role: discord.Role
    verified_role_grantable: bool
    verified_role_reasons: list[SettingsValidationTag]
    domains: list[str]

    def __init__(self):
        self.log_channel_reasons = []
        self.verified_role_reasons = []

    @property
    def is_valid(self):
        log_channel_availability = (
            self.log_channel_sendable if self.log_channel else False
        )
        verified_role_availability = (
            self.verified_role_grantable if self.verified_role else False
        )
        return all((log_channel_availability, verified_role_availability))
