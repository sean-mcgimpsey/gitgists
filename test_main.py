from fastapi.testclient import TestClient
from .main import app, GistParams, UserGistReduced

# Simple test that the root endpoint comes up and returns the expected message.
def test_root_endpoint():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API to return a users public gists"}

# Test that the list_user_gists endpoint returns a list of gists for a valid username. 
def test_list_user_gists():
    client = TestClient(app)
    params = GistParams(username="octocat", per_page=5, page=1)
    response = client.get(f"/{params.username}", params=params.dict())
    assert response.status_code == 200
    gists = response.json()
    assert isinstance(gists, list)
    for gist in gists:
        assert "url" in gist
        assert "id" in gist
        assert "description" in gist
        assert "created_at" in gist
        assert "updated_at" in gist

# Test that the private endpoint returns a 401 Unauthorized error when no token is provided.
def test_private_endpoint_no_token():
    client = TestClient(app)
    params = GistParams(username="octocat", per_page=5, page=1)
    response = client.get(f"/private/{params.username}", params=params.dict())
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing Bearer Token"}