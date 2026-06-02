# test_api.py — Unit and integration tests for the GitHub Gists API.
#
# Unit tests use a mock HTTP client so they run offline and are fast.
# The final test (test_get_octocat_gists_live) calls the real GitHub API
# and requires an internet connection.

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

# TestClient wraps the FastAPI app so we can make HTTP requests in tests
# without starting a real server
client = TestClient(app)


# Helper that builds a fake gist dict matching the shape GitHub returns.
# Default values are provided so individual tests only override what they care about.
def make_gist(id="abc123", description="A test gist", filename="hello.py"):
    return {
        "id": id,
        "description": description,
        "html_url": f"https://gist.github.com/{id}",
        "created_at": "2021-01-01T00:00:00Z",
        "updated_at": "2021-06-01T00:00:00Z",
        # GitHub represents files as a dict keyed by filename
        "files": {filename: {"filename": filename}},
    }


# Minimal stand-in for an httpx.Response — only the fields our code reads
class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json


# Shared fixture: two sample gists reused by multiple tests
@pytest.fixture
def mock_github_gists():
    return [make_gist("1", "First gist", "one.py"), make_gist("2", "Second gist", "two.py")]


# Verify the endpoint returns an HTTP 200 and a list with the correct number of items
def test_get_user_gists_returns_list(mock_github_gists):
    async def fake_get(*args, **kwargs):
        return MockResponse(200, mock_github_gists)

    with patch("httpx.AsyncClient.get", new=fake_get):
        response = client.get("/octocat")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


# Verify each gist in the response has the expected fields and correct types
def test_get_user_gists_shape(mock_github_gists):
    async def fake_get(*args, **kwargs):
        return MockResponse(200, mock_github_gists)

    with patch("httpx.AsyncClient.get", new=fake_get):
        response = client.get("/octocat")

    gist = response.json()[0]
    assert "id" in gist
    assert "description" in gist
    assert "html_url" in gist
    assert "created_at" in gist
    assert "updated_at" in gist
    assert "files" in gist
    # "files" should be a list of filenames, not the raw GitHub dict
    assert isinstance(gist["files"], list)


# Verify that a 404 from GitHub is forwarded as a 404 to the caller
def test_get_user_gists_unknown_user():
    async def fake_get(*args, **kwargs):
        return MockResponse(404, {"message": "Not Found"})

    with patch("httpx.AsyncClient.get", new=fake_get):
        response = client.get("/this-user-does-not-exist-xyz")

    assert response.status_code == 404


# Verify that a user with no gists returns 200 with an empty list (not an error)
def test_get_user_gists_empty_list():
    async def fake_get(*args, **kwargs):
        return MockResponse(200, [])

    with patch("httpx.AsyncClient.get", new=fake_get):
        response = client.get("/userwithnogists")

    assert response.status_code == 200
    assert response.json() == []


# Integration test — calls the real GitHub API.
# Requires internet access; skip in offline / CI environments if needed.
def test_get_octocat_gists_live():
    """Integration test — calls the real GitHub API."""
    response = client.get("/octocat")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        gist = data[0]
        assert "id" in gist
        assert "html_url" in gist
        assert "files" in gist
