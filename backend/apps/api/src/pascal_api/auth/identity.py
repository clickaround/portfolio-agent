"""Verify Supabase sessions at the authentication boundary."""
import json
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import HTTPException, Request


def current_user(request: Request) -> str | None:
    settings = request.app.state.settings
    if not settings.auth_url:
        return None
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    verifier = getattr(request.app.state, "verify_token", None)
    if verifier:
        user_id = verifier(token)
    else:
        try:
            req = UrlRequest(settings.auth_url.rstrip("/") + "/auth/v1/user", headers={"Authorization": f"Bearer {token}", "apikey": settings.auth_key})
            with urlopen(req, timeout=10) as response:
                user_id = json.load(response).get("id")
        except HTTPError as exc:
            raise HTTPException(status_code=401 if exc.code in (401, 403) else 503, detail="Authentication unavailable or invalid") from None
        except (URLError, TimeoutError, ValueError):
            raise HTTPException(status_code=503, detail="Authentication unavailable") from None
    try:
        return str(uuid.UUID(user_id))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=401, detail="Invalid session") from None


