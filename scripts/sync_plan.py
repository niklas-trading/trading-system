import os
import re
import requests
from datetime import datetime

TOKEN = os.environ["GITHUB_TOKEN"]
OWNER = os.environ["OWNER"]        # niklas-trading
REPO = os.environ["REPO_NAME"]     # trading-system
PROJECT_NUMBER = int(os.environ["PROJECT_NUMBER"])

API_URL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

def graphql(query, variables=None):
    resp = requests.post(
        API_URL,
        headers=HEADERS,
        json={"query": query, "variables": variables or {}},
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]

# 1. Repository Project holen
data = graphql(
    """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        projectV2(number: $number) {
          id
          fields(first: 20) {
            nodes {
              ... on ProjectV2Field {
                id
                name
              }
              ... on ProjectV2SingleSelectField {
                id
                name
                options {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
    """,
    {"owner": OWNER, "repo": REPO, "number": PROJECT_NUMBER},
)

project = data["repository"]["projectV2"]
if project is None:
    raise RuntimeError("Project not found. Check PROJECT_NUMBER.")

PROJECT_ID = project["id"]

field_ids = {}
status_options = {}

for field in project["fields"]["nodes"]:
    if field["name"] in ("Start", "End", "Status"):
        field_ids[field["name"]] = field["id"]
        if field["name"] == "Status":
            for opt in field["options"]:
                status_options[opt["name"]] = opt["id"]

# 2. Jahresplan lesen
with open("docs/year-plan.md", encoding="utf-8") as f:
    text = f.read()

weeks = re.split(r"(?=## Woche \d+)", text)

for block in weeks:
    if not block.startswith("## Woche"):
        continue

    title = block.splitlines()[0].replace("## ", "").strip()

    date_match = re.search(
        r"\*\*Zeitraum:\*\*\s*([0-9.]+)\s*[–-]\s*([0-9.]+)", block
    )
    if not date_match:
        continue

    start = datetime.strptime(date_match.group(1), "%d.%m.%Y").date().isoformat()
    end = datetime.strptime(date_match.group(2), "%d.%m.%Y").date().isoformat()

    # 3. Issue erstellen
    issue_resp = requests.post(
        f"https://api.github.com/repos/{OWNER}/{REPO}/issues",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
        },
        json={
            "title": title,
            "body": block,
            "labels": ["week"],
        },
    )
    issue_resp.raise_for_status()
    issue = issue_resp.json()
    content_id = issue["node_id"]

    # 4. Issue dem Project hinzufügen
    item_id = graphql(
        """
        mutation($project: ID!, $content: ID!) {
          addProjectV2ItemById(
            input: { projectId: $project, contentId: $content }
          ) {
            item {
              id
            }
          }
        }
        """,
        {"project": PROJECT_ID, "content": content_id},
    )["addProjectV2ItemById"]["item"]["id"]

    # 5. Start / End setzen
    for name, value in {"Start": start, "End": end}.items():
        graphql(
            """
            mutation($project: ID!, $item: ID!, $field: ID!, $value: Date!) {
              updateProjectV2ItemFieldValue(
                input: {
                  projectId: $project
                  itemId: $item
                  fieldId: $field
                  value: { date: $value }
                }
              ) {
                projectV2Item { id }
              }
            }
            """,
            {
                "project": PROJECT_ID,
                "item": item_id,
                "field": field_ids[name],
                "value": value,
            },
        )

    # 6. Status = Backlog
    graphql(
        """
        mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
          updateProjectV2ItemFieldValue(
            input: {
              projectId: $project
              itemId: $item
              fieldId: $field
              value: { singleSelectOptionId: $option }
            }
          ) {
            projectV2Item { id }
          }
        }
        """,
        {
            "project": PROJECT_ID,
            "item": item_id,
            "field": field_ids["Status"],
            "option": status_options["Backlog"],
        },
    )

    print(f"Synced week: {title}")
