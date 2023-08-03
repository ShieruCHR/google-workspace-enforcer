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
            return ""

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
        return domain in self.allowed_domains
