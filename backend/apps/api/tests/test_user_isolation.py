from fastapi.testclient import TestClient
from pascal_api.config import Settings
from pascal_api.main import create_app


def test_authenticated_users_have_separate_projects_and_jobs(tmp_path):
    settings = Settings(tmp_path, "claude", 10, 30, 1, ("http://localhost",), auth_url="https://example.invalid", auth_key="public")
    app = create_app(settings)
    app.state.verify_token = lambda token: {"alice": "11111111-1111-4111-8111-111111111111", "bob": "22222222-2222-4222-8222-222222222222"}.get(token)
    with TestClient(app) as client:
        alice = {"Authorization": "Bearer alice"}
        bob = {"Authorization": "Bearer bob"}
        assert client.get("/projects").status_code == 401
        assert client.get("/projects", headers={"Authorization": "Bearer invalid"}).status_code == 401
        assert client.post("/projects", headers=alice, json={"id": "private", "title": "Private"}).status_code == 201
        assert client.post("/projects/private/assets/images", headers=alice, files={"file": ("secret.png", b"private bytes", "image/png")}).status_code == 201
        assert client.get("/projects/private", headers=bob).status_code == 404
        assert client.get("/projects", headers=bob).json() == []
        assert client.get("/projects/private/brief", headers=bob).status_code == 404
        assert client.get("/projects/private/files/images/secret.png", headers=bob).status_code == 404
        assert client.get("/projects/private/files/images/secret.png", headers=alice).content == b"private bytes"
        assert client.get("/jobs", headers=bob).json() == []
        job = app.state.user_stores["11111111-1111-4111-8111-111111111111"][1].submit("test", "private", lambda log: {})
        assert client.get(f"/jobs/{job['id']}", headers=bob).status_code == 404
        assert client.get(f"/jobs/{job['id']}", headers=alice).status_code == 200
        assert client.get("/projects/private", headers=alice).status_code == 200
