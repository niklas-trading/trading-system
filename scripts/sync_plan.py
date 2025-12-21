import os
import re
import requests
from datetime import datetime

TOKEN = os.environ["GITHUB_TOKEN"]
ORG = os.environ["ORG"]
PROJECT_NUMBER = int(os.environ["PROJECT_NUMBER"])
REPO = os.environ["REPO"]

API_URL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

def graphql(query, variables=None):
    r = requests.post(
        API_URL,
        headers=HEADERS,
        json={"query": query, "variables": variables or {}},
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]

# 1. Org Project holen
data = graphql(
    """
    query($org: String!, $number: Int!) {
      organization(login: $org) {
        projectV2(number: $number) {
          id
          fields(first: 30) {
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
    {"org": ORG, "number": PROJECT_NUMBER},
)

project = data["organization"]["projectV2"]
if project is None:
    raise RuntimeError("Project not found – check PROJECT_NUMBER and PAT permissions")

PROJECT_ID = project["id"]

field_ids = {}
status_options = {}

for f in project["fields"]["nodes"]:
    if f["name"] in ("Start", "End", "Status"):
        field_ids[f["name"]] = f["id"]
        if f["name"] == "Status":
            for opt in f["options"]:
                status_options[opt["name"]] = opt["id"]

# 2. Jahresplan lesen
with open("docs/year-plan.md", encoding="utf-8") as f:
    text = f.read()

weeks = re.split(r"(?=## Woche \d+)", text)

for block in weeks:
    if not block.startswith("## Woche"):
        continue

    title = block.splitlines()[0].replace("## ", "").strip()

    m = re.search(r"\*\*Zeitraum:\*\*\s*([0-9.]+)\s*[–-]\s*([0-9.]+)", block)
    if not m:
        continue

    start = datetime.strptime(m.group(1), "%d.%m.%Y").date().isoformat()
    end = datetime.strptime(m.group(2), "%d.%m.%Y").date().isoformat()

    # 3. Issue erstellen
    issue = requests.post(
        f"https://api.github.com/repos/{ORG}/{REPO}/issues",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={"title": title, "body": block, "labels": ["week"]},
    ).json()

    content_id = issue["node_id"]

    # 4. Issue ins Project
    item_id = graphql(
        """
        mutation($project: ID!, $content: ID!) {
          addProjectV2ItemById(
            input: { projectId: $project, contentId: $content }
          ) {
            item { id }
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
              ) { projectV2Item { id } }
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
          ) { projectV2Item { id } }
        }
        """,
        {
            "project": PROJECT_ID,
            "item": item_id,
            "field": field_ids["Status"],
            "option": status_options["Backlog"],
        },
    )

    print(f"Created & synced: {title}")
