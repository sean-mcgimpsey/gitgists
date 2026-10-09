from fastapi import Depends, FastAPI, Response, Query, HTTPException, params, status
from fastapi.concurrency import asynccontextmanager
from fastapi.security import OAuth2PasswordBearer
import httpx
import json
from pydantic import BaseModel, Field
from typing import Annotated 



''' Example of a Gist JSON response from GitHub API (list of gists for a user):
  {
    "url": "https://api.github.com/gists/6cad326836d38bd3a7ae",
    "forks_url": "https://api.github.com/gists/6cad326836d38bd3a7ae/forks",
    "commits_url": "https://api.github.com/gists/6cad326836d38bd3a7ae/commits",
    "id": "6cad326836d38bd3a7ae",
    "node_id": "MDQ6R2lzdDZjYWQzMjY4MzZkMzhiZDNhN2Fl",
    "git_pull_url": "https://gist.github.com/6cad326836d38bd3a7ae.git",
    "git_push_url": "https://gist.github.com/6cad326836d38bd3a7ae.git",
    "html_url": "https://gist.github.com/octocat/6cad326836d38bd3a7ae",
    "files": {
      "hello_world.rb": {
        "filename": "hello_world.rb",
        "type": "application/x-ruby",
        "language": "Ruby",
        "raw_url": "https://gist.githubusercontent.com/octocat/6cad326836d38bd3a7ae/raw/db9c55113504e46fa076e7df3a04ce592e2e86d8/hello_world.rb",
        "size": 175
      }
    },
    "public": true,
    "created_at": "2014-10-01T16:19:34Z",
    "updated_at": "2026-10-09T10:20:01Z",
    "description": "Hello world!",
    "comments": 297,
    "user": null,
    "comments_enabled": true,
    "comments_url": "https://api.github.com/gists/6cad326836d38bd3a7ae/comments",
    "owner": {
      "login": "octocat",
      "id": 583231,
      "node_id": "MDQ6VXNlcjU4MzIzMQ==",
      "avatar_url": "https://avatars.githubusercontent.com/u/583231?v=4",
      "gravatar_id": "",
      "url": "https://api.github.com/users/octocat",
      "html_url": "https://github.com/octocat",
      "followers_url": "https://api.github.com/users/octocat/followers",
      "following_url": "https://api.github.com/users/octocat/following{/other_user}",
      "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
      "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
      "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
      "organizations_url": "https://api.github.com/users/octocat/orgs",
      "repos_url": "https://api.github.com/users/octocat/repos",
      "events_url": "https://api.github.com/users/octocat/events{/privacy}",
      "received_events_url": "https://api.github.com/users/octocat/received_events",
      "type": "User",
      "user_view_type": "public",
      "site_admin": false
    },
    "truncated": false
  }
'''

# Example of a reduced Pydantic model for a GitHub Gist, containing only the fields we want to expose in our API response.
class UserGistReduced(BaseModel):
    url: str
    id: str
    public: bool
    description: str | None = None
    comments: int
    forks_url: str
    created_at: str
    updated_at: str

# Define a Pydantic model for the query parameters used in the API endpoints. 
# This model will validate the input parameters and provide default values where necessary.
class GistParams(BaseModel):
    username: str = Field(..., description="GitHub username to fetch gists for")
    per_page: int = Field(10, description="Number of gists to return per page (default is 10)")
    page: int = Field(1, description="Page number to return (default is 1)")

# Use an async context manager to manage the lifespan of the FastAPI app, including startup and shutdown tasks.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform any startup tasks here
    app.state.client = httpx.AsyncClient(
        base_url="https://api.github.com",
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28"
            }
    )
    yield
    # Perform any shutdown tasks here
    await app.state.client.aclose()

app = FastAPI(title="GitHub Gists API", description="API to return a users public gists", version="1.0.0", lifespan=lifespan)
oauth_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# For example purposes, we will use a hardcoded Bearer token. 
BEARER_TOKEN = "superbearer"

# Re-usable function to fetch user gists from GitHub API. 
async def get_user_gists(params: GistParams = Query()) -> list[UserGistReduced]:
    http_client: httpx.AsyncClient = app.state.client
    try:
        response = await http_client.get(f"/users/{params.username}/gists", params={"per_page": params.per_page, "page": params.page})

    except httpx.RequestError as err:
        return {"error": f"An error occurred while requesting gists for user {params.username}: {err}"}  
    gists = response.json() 
    return gists 

# Routes
@app.get("/")
async def root():
    return {"message": "API to return a users public gists"}


async def verify_bearer_token(token: Annotated[str, Depends(oauth_scheme)]):
    if not token or token != BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Bearer Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# Public endpoint that does not require authentication.
# Example: curl http://localhost:8000/users?username=octocat
@app.get("/{username}")
async def list_user_gists(params: GistParams = Query()):
    return await get_user_gists(params)


# Private endpoint that requires a valid Bearer token.
# Example: curl -H "Authorization: Bearer superbearer" http://localhost:8000/private/users?username=octocat
@app.get("/private/{username}")
async def list_user_gists(token: Annotated[str, Depends(verify_bearer_token)], params: GistParams = Query()) -> list[UserGistReduced]:
    return await get_user_gists(params) 
