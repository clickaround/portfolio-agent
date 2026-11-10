"""User-scoped Supabase conversation operations.

The caller supplies the user's verified session token. This adapter never uses
an admin key and is not wired to production routes until project identity and
the worker write boundary are implemented.
"""
import json
import uuid
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class ConversationStoreError(Exception):
    """A conversation operation failed without exposing response data or keys."""


def _http_transport(request: Request) -> tuple[int, bytes]:
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, response.read(65537)
    except HTTPError as exc:
        return exc.code, b""
    except (URLError, TimeoutError, OSError) as exc:
        raise ConversationStoreError("Conversation storage unavailable") from exc


class SupabaseConversationRepository:
    def __init__(self, base_url: str, publishable_key: str, transport: Callable = _http_transport):
        parsed = urlsplit(base_url)
        if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}):
            raise ValueError("Supabase URL must use HTTPS or local loopback")
        if not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment or not publishable_key:
            raise ValueError("Invalid Supabase configuration")
        self._url = base_url.rstrip("/")
        self._key = publishable_key
        self._transport = transport

    def append_user_message(self, token: str, conversation_id: str, request_id: str, text: str) -> str:
        if not token or not text or not text.strip() or len(text) > 4000:
            raise ConversationStoreError("Invalid conversation request")
        try:
            conversation = str(uuid.UUID(conversation_id))
            request_id = str(uuid.UUID(request_id))
        except (ValueError, AttributeError, TypeError) as exc:
            raise ConversationStoreError("Invalid conversation request") from exc
        payload = json.dumps({"p_conversation_id": conversation, "p_request_id": request_id, "p_text": text}).encode("utf-8")
        request = Request(self._url + "/rest/v1/rpc/append_user_message", data=payload, method="POST", headers={
            "apikey": self._key, "Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json",
        })
        status, data = self._transport(request)
        if status != 200 or len(data) > 65536:
            raise ConversationStoreError("Conversation request was not accepted")
        try:
            return str(uuid.UUID(json.loads(data)))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ConversationStoreError("Invalid conversation storage response") from exc
