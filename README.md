# GitHub Gists API

A simple HTTP web server that exposes a user's public GitHub Gists via a REST endpoint.

## Endpoint

```
GET /<username>
```

Returns a list of public Gists for the given GitHub username.

**Example response:**
```json
[
  {
    "id": "aa5a315d61ae9438b18d",
    "description": "Hello World",
    "html_url": "https://gist.github.com/aa5a315d61ae9438b18d",
    "created_at": "2010-04-14T02:15:15Z",
    "updated_at": "2011-06-20T11:34:15Z",
    "files": ["hello_world.rb"]
  }
]
```

Returns `404` if the GitHub user does not exist.

---

## Running locally

### Prerequisites
- Python 3.10+

### Setup

```bash
pip install -r requirements.txt
```

### Start the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

The API is available at `http://localhost:8080/<username>`.

**Example:**
```bash
curl http://localhost:8080/octocat
```

---

## Running tests

```bash
pytest tests/
```

---

## Running with Docker

### Build the image

```bash
docker build -t gists-api .
```

### Run the container

```bash
docker run -p 8080:8080 gists-api
```

The API is available at `http://localhost:8080/<username>`.
