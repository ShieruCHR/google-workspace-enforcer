import os

from dotenv import load_dotenv

load_dotenv()
allowed_domains = os.getenv("DOMAINS", "").split(",")


def is_allowed(domain: str):
    if os.getenv("DOMAINS", None) is None:
        return True
    return domain in allowed_domains


def friendly_allowed_domains():
    return ", ".join(allowed_domains)
