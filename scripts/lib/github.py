import os
import time
import requests

API_URL = "https://api.github.com/graphql"

TOKEN = os.environ["GITHUB_TOKEN"]
REST_HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}
GRAPHQL_HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

def graphql(query, variables=None, retries=3):
    for i in range(retries):
        r = requests.post(
            API_URL,
            headers=GRAPHQL_HEADERS,
            json={"query": query, "variables": variables or {}},
        )
        data = r.json()
        if "errors" not in data:
            return data["data"]
        if i == retries - 1:
            raise RuntimeError(data["errors"])
        time.sleep(1 + i)

def rest(method, url, **kwargs):
    r = requests.request(method, url, headers=REST_HEADERS, **kwargs)
    r.raise_for_status()
    return r.json()
