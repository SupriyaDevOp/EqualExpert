# main.py — FastAPI application that exposes GitHub Gist data via a REST API.
# It proxies requests to the GitHub API and returns a simplified gist summary.

from fastapi import FastAPI, HTTPException
import httpx

# Create the FastAPI application instance
app = FastAPI()


# Health check endpoint — used by load balancers and monitoring tools
# to confirm the service is running
@app.get("/health")
async def health():
    return {"status": "ok"}


# Base URL for all GitHub REST API calls
GITHUB_API_BASE = "https://api.github.com"

# Headers required by GitHub API:
#   Accept         — requests the stable v3 JSON format
#   X-GitHub-Api-Version — pins the API version so behaviour doesn't change
#                          if GitHub releases a new version
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# Route: GET /{username}
# Returns a list of public gists for the given GitHub username.
# Each item in the list contains only the fields we care about;
# the full GitHub response is intentionally trimmed down.
@app.get("/{username}")
async def get_user_gists(username: str):
    # Use an async HTTP client so the server can handle other requests
    # while waiting for the GitHub API to respond
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GITHUB_API_BASE}/users/{username}/gists",
            headers=GITHUB_HEADERS,
        )

    # GitHub returns 404 when the username doesn't exist
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    # Any other non-200 status means something went wrong on GitHub's side
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="GitHub API error",
        )

    gists = response.json()

    # Transform each raw gist object into a smaller, cleaner shape.
    # "files" is a dict keyed by filename in the GitHub response;
    # we convert it to a plain list of filenames for easier consumption.
    return [
        {
            "id": gist["id"],
            "description": gist["description"],
            "html_url": gist["html_url"],
            "created_at": gist["created_at"],
            "updated_at": gist["updated_at"],
            "files": list(gist["files"].keys()),  # extract filenames only
        }
        for gist in gists
    ]
