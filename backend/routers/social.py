from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Literal
from urllib.parse import urlencode
import httpx, os, re, secrets

from database import get_db
from models.user import User
from deps import get_current_user

router = APIRouter(prefix="/social", tags=["social"])

SECRET_KEY      = os.getenv("SECRET_KEY")
REDIRECT_BASE   = os.getenv("SOCIAL_OAUTH_REDIRECT_BASE")   # ex: https://api.junglegap.fr
FRONTEND_BASE   = os.getenv("FRONTEND_BASE_URL")            # ex: https://junglegap.fr
DISCORD_ID      = os.getenv("DISCORD_CLIENT_ID")
DISCORD_SECRET  = os.getenv("DISCORD_CLIENT_SECRET")
TWITCH_ID       = os.getenv("TWITCH_CLIENT_ID")
TWITCH_SECRET   = os.getenv("TWITCH_CLIENT_SECRET")

# ─── Helpers ────────────────────────────────────────────────

def _make_state(user_id: int) -> str:
    """JWT signé contenant user_id + nonce + exp 10min. Anti-CSRF."""
    payload = {
        "uid":   user_id,
        "nonce": secrets.token_urlsafe(16),
        "exp":   datetime.utcnow() + timedelta(minutes=10),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def _decode_state(state: str) -> int:
    try:
        payload = jwt.decode(state, SECRET_KEY, algorithms=["HS256"])
        return int(payload["uid"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(400, "State invalide ou expiré")

def _redirect_front(status: Literal["ok", "err"], platform: str, reason: str = "") -> RedirectResponse:
    qs = urlencode({"social": f"{platform}_{status}", **({"reason": reason} if reason else {})})
    return RedirectResponse(f"{FRONTEND_BASE}/settings?{qs}")

# ─── GET /social/discord/connect ────────────────────────────

@router.get("/discord/connect")
def discord_connect(current_user: User = Depends(get_current_user)):
    state = _make_state(current_user.id)
    params = {
        "client_id":     DISCORD_ID,
        "redirect_uri":  f"{REDIRECT_BASE}/social/discord/callback",
        "response_type": "code",
        "scope":         "identify",
        "state":         state,
        "prompt":        "consent",
    }
    return {"url": f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"}

# ─── GET /social/discord/callback ───────────────────────────

@router.get("/discord/callback")
async def discord_callback(
    code:  str = Query(...),
    state: str = Query(...),
    db:    Session = Depends(get_db),
):
    try:
        user_id = _decode_state(state)
    except HTTPException:
        return _redirect_front("err", "discord", "state_invalid")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return _redirect_front("err", "discord", "user_not_found")

    redirect_uri = f"{REDIRECT_BASE}/social/discord/callback"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            tok_resp = await client.post(
                "https://discord.com/api/oauth2/token",
                data={
                    "client_id":     DISCORD_ID,
                    "client_secret": DISCORD_SECRET,
                    "grant_type":    "authorization_code",
                    "code":          code,
                    "redirect_uri":  redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if tok_resp.status_code != 200:
                return _redirect_front("err", "discord", "token_exchange_failed")
            access_token = tok_resp.json().get("access_token")

            me_resp = await client.get(
                "https://discord.com/api/users/@me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if me_resp.status_code != 200:
                return _redirect_front("err", "discord", "fetch_user_failed")
            me = me_resp.json()
    except Exception:
        return _redirect_front("err", "discord", "network")

    discord_id_str = str(me["id"])
    display = me.get("global_name") or me.get("username") or "unknown"

    # Vérif unicité : ce Discord ID n'est pas déjà lié à un autre user
    existing = db.query(User).filter(
        User.discord_id == discord_id_str,
        User.id != user.id,
    ).first()
    if existing:
        return _redirect_front("err", "discord", "already_linked")

    user.discord_id          = discord_id_str
    user.discord_username    = display
    user.discord_verified_at = datetime.utcnow()
    db.commit()

    return _redirect_front("ok", "discord")

# ─── GET /social/twitch/connect ─────────────────────────────

@router.get("/twitch/connect")
def twitch_connect(current_user: User = Depends(get_current_user)):
    state = _make_state(current_user.id)
    params = {
        "client_id":     TWITCH_ID,
        "redirect_uri":  f"{REDIRECT_BASE}/social/twitch/callback",
        "response_type": "code",
        "scope":         "",
        "state":         state,
        "force_verify":  "true",
    }
    return {"url": f"https://id.twitch.tv/oauth2/authorize?{urlencode(params)}"}

# ─── GET /social/twitch/callback ────────────────────────────

@router.get("/twitch/callback")
async def twitch_callback(
    code:  str = Query(...),
    state: str = Query(...),
    db:    Session = Depends(get_db),
):
    try:
        user_id = _decode_state(state)
    except HTTPException:
        return _redirect_front("err", "twitch", "state_invalid")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return _redirect_front("err", "twitch", "user_not_found")

    redirect_uri = f"{REDIRECT_BASE}/social/twitch/callback"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            tok_resp = await client.post(
                "https://id.twitch.tv/oauth2/token",
                data={
                    "client_id":     TWITCH_ID,
                    "client_secret": TWITCH_SECRET,
                    "grant_type":    "authorization_code",
                    "code":          code,
                    "redirect_uri":  redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if tok_resp.status_code != 200:
                return _redirect_front("err", "twitch", "token_exchange_failed")
            access_token = tok_resp.json().get("access_token")

            me_resp = await client.get(
                "https://api.twitch.tv/helix/users",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Client-Id":     TWITCH_ID,
                },
            )
            if me_resp.status_code != 200:
                return _redirect_front("err", "twitch", "fetch_user_failed")
            data = me_resp.json().get("data", [])
            if not data:
                return _redirect_front("err", "twitch", "empty_user")
            me = data[0]
    except Exception:
        return _redirect_front("err", "twitch", "network")

    twitch_id_str = str(me["id"])
    login = me.get("login") or "unknown"

    existing = db.query(User).filter(
        User.twitch_id == twitch_id_str,
        User.id != user.id,
    ).first()
    if existing:
        return _redirect_front("err", "twitch", "already_linked")

    user.twitch_id          = twitch_id_str
    user.twitch_username    = login
    user.twitch_verified_at = datetime.utcnow()
    db.commit()

    return _redirect_front("ok", "twitch")

# ─── POST /social/links (X + Instagram) ─────────────────────

# X: 4-15 chars, lettres/chiffres/underscore
X_REGEX  = re.compile(r"^[A-Za-z0-9_]{4,15}$")
# Instagram: 1-30 chars, lettres/chiffres/point/underscore, pas de point en début/fin ni double point
IG_REGEX = re.compile(r"^(?!\.)(?!.*\.\.)[A-Za-z0-9._]{1,30}(?<!\.)$")

class LinksSchema(BaseModel):
    x_handle:         str | None = None
    instagram_handle: str | None = None

@router.post("/links")
def set_links(
    body: LinksSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.x_handle is not None:
        h = body.x_handle.strip().lstrip("@")
        if h == "":
            current_user.x_handle = None
        elif X_REGEX.match(h):
            current_user.x_handle = h
        else:
            raise HTTPException(400, "Handle X invalide (4-15 caractères, lettres/chiffres/_)")

    if body.instagram_handle is not None:
        h = body.instagram_handle.strip().lstrip("@")
        if h == "":
            current_user.instagram_handle = None
        elif IG_REGEX.match(h):
            current_user.instagram_handle = h
        else:
            raise HTTPException(400, "Handle Instagram invalide")

    db.commit()
    return {
        "x_handle":         current_user.x_handle,
        "instagram_handle": current_user.instagram_handle,
    }

# ─── DELETE /social/{platform} ──────────────────────────────

@router.delete("/{platform}")
def unlink(
    platform: Literal["discord", "twitch", "x", "instagram"],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if platform == "discord":
        current_user.discord_id          = None
        current_user.discord_username    = None
        current_user.discord_verified_at = None
    elif platform == "twitch":
        current_user.twitch_id          = None
        current_user.twitch_username    = None
        current_user.twitch_verified_at = None
    elif platform == "x":
        current_user.x_handle = None
    elif platform == "instagram":
        current_user.instagram_handle = None
    db.commit()
    return {"success": True}