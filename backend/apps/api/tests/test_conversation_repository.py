import json
import uuid

import pytest
from pascal_api.conversations.repository import ConversationStoreError, SupabaseConversationRepository


def test_append_uses_user_token_and_returns_message_id():
    calls = []
    message_id = str(uuid.uuid4())

    def transport(request):
        calls.append(request)
        return 200, json.dumps(message_id).encode()

    repo = SupabaseConversationRepository("https://example.invalid", "publishable", transport)
    conversation_id, request_id = str(uuid.uuid4()), str(uuid.uuid4())
    assert repo.append_user_message("user-token", conversation_id, request_id, "hello") == message_id
    assert calls[0].get_header("Authorization") == "Bearer user-token"
    assert json.loads(calls[0].data) == {"p_conversation_id": conversation_id, "p_request_id": request_id, "p_text": "hello"}


def test_invalid_server_result_and_no_session_fail_closed():
    repo = SupabaseConversationRepository("https://example.invalid", "publishable", lambda request: (200, b'"not-a-uuid"'))
    with pytest.raises(ConversationStoreError):
        repo.append_user_message("user-token", str(uuid.uuid4()), str(uuid.uuid4()), "hello")
    with pytest.raises(ConversationStoreError):
        repo.append_user_message("", str(uuid.uuid4()), str(uuid.uuid4()), "hello")


def test_http_failure_does_not_expose_upstream_response_or_token():
    repo = SupabaseConversationRepository("https://example.invalid", "publishable", lambda request: (403, b"sensitive provider data"))
    with pytest.raises(ConversationStoreError) as error:
        repo.append_user_message("user-secret-token", str(uuid.uuid4()), str(uuid.uuid4()), "hello")
    assert "user-secret-token" not in str(error.value)
    assert "sensitive provider data" not in str(error.value)
