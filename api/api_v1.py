import os
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, RedirectResponse
from urllib import parse
import requests
from sqlmodel import Session
from database import get_session

from shared import bot, processing_states
import settings_utils


router = APIRouter()

redirect_host = os.getenv("HOST")
discord_redirect_uri = redirect_host + "/discord/callback"
discord_api_endpoint = "https://discord.com/api/v10"
google_redirect_uri = redirect_host + "/google/callback"
google_api_endpoint = "https://www.googleapis.com/oauth2/v4"


@router.get("/discord/auth")
async def discord_oauth2(state: str):
    DISCORD_AUTHORIZATION_URL = "https://discord.com/oauth2/authorize/?"

    if state not in processing_states:
        return "There's no data for this state. Please try again!"

    parameters = {
        "response_type": "code",
        "client_id": os.getenv("DISCORD_CLIENT_ID"),
        "scope": "identify",
        "state": state,
        "redirect_uri": discord_redirect_uri,
        "prompt": "consent",
    }

    return RedirectResponse(DISCORD_AUTHORIZATION_URL + parse.urlencode(parameters))


@router.get("/discord/callback")
async def discord_callback(code: str, state: str):
    discord_user_data = {
        "client_id": os.getenv("DISCORD_CLIENT_ID"),
        "client_secret": os.getenv("DISCORD_CLIENT_SECRET"),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": discord_redirect_uri,
    }
    discord_token = requests.post(
        discord_api_endpoint + "/oauth2/token", data=discord_user_data
    )
    discord_token.raise_for_status()
    discord_user = requests.get(
        discord_api_endpoint + "/users/@me",
        headers={"Authorization": f"Bearer {discord_token.json()['access_token']}"},
    )
    discord_user_data = discord_user.json()
    processing_states[state]["discord"] = {
        "id": discord_user_data["id"],
        "username": discord_user_data["username"],
        "global_name": discord_user_data["global_name"],
    }
    return RedirectResponse("/" + state)


@router.get("/google/auth")
async def google_oauth2(state: str):
    GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth?"

    if state not in processing_states:
        return "There's no data for this state. Please try again!"
    parameters = {
        "response_type": "code",
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "scope": "email",
        "redirect_uri": google_redirect_uri,
        "state": state,
    }

    return RedirectResponse(GOOGLE_AUTHORIZATION_URL + parse.urlencode(parameters))


@router.get("/google/callback")
async def google_callback(code: str, state: str):
    google_user_data = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": google_redirect_uri,
    }
    google_token = requests.post(
        "https://oauth2.googleapis.com/token", data=google_user_data
    )
    google_token.raise_for_status()
    google_user = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo?access_token="
        + google_token.json()["access_token"]
    )
    google_user_data = google_user.json()
    processing_states[state]["google"] = {
        "email": google_user_data["email"],
        "organization": google_user_data.get("hd"),
    }
    return RedirectResponse("/" + state)


@router.get("/session/{session_id}")
async def get_session_id(session_id: str):
    return processing_states[session_id]


@router.get("/validate")
async def validate(state: str, session: Session = Depends(get_session)):
    if state not in processing_states:
        return "There's no data for this state. Please try again!"

    settings = settings_utils.get_settings(
        session, processing_states[state]["guild_id"]
    )
    if processing_states[state]["google"] and processing_states[state]["discord"]:
        if not settings.is_allowed(
            processing_states[state]["google"]["organization"],
        ):
            return "This domain is not allowed."
        channel = bot.get_channel(int(settings.verification_log_channel_id))
        user = bot.get_user(int(processing_states[state]["discord"]["id"]))
        role = channel.guild.get_role(int(settings.verified_role_id))
        await channel.guild.get_member(user.id).add_roles(
            role, reason="Verification completed."
        )
        await channel.send(f"{user.mention}さんの認証が完了しました！")
        del processing_states[state]
        return RedirectResponse("/success")

    return "Validation failed."


@router.get("/{state}")
async def auth_page(state: str):
    if state == "success":
        return FileResponse("success.html")
    return FileResponse("main.html")
