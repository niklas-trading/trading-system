import os
import re
import requests
from datetime import datetime

TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["REPO"]
ORG = os.environ["ORG"]
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
    return resp.json()["data"]

# 1. Project + Fields holen
data = graphql(
    """
    query($org: String!, $number: Int!) {
      organization(login: $org) {
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
    {"org": ORG, "number": PROJECT_NUMBER},
)

project = data["organization"]["projectV2"]
PROJECT_ID = project["id"]

field_ids = {}
status_options = {}

for field in project["fields"]["nodes"]:
    if field["name"] in ("Start", "End", "Status"):
        field_ids[field["name"]] = field["id"]
        if field["name"] == "Status":
            for opt in field["options"]:
                status_options[opt["name"]] = opt["id"]

# 2. Year plan lesen
with open("docs/year-plan.md", encoding="utf-8") as f:
    text = f.read()

weeks = re.split(r"(?=## Woche \d+)", text)

for block in weeks:
    if not block.startswith("## Woche"):
        continue

    title = block.splitlines()[0].replace("## ", "").strip()

    date_match = re.search(
        r"\*\*Zeitraum:\*\*\s*([0-9.]+)\s*[-–]\s*([0-9.]+)", block
    )
    if not date_match:
        continue

    start = datetime.strptime(date_match.group(1), "%d.%m.%Y").date().isoformat()
    end = datetime.strptime(date_match.group(2), "%d.%m.%Y").date().isoformat()

    # 3. Issue erstellen
    issue_resp = requests.post(
        f"https://api.github.com/repos/{REPO}/issues",
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

    # Node ID holen
    node_id = graphql(
        """
        query($id: ID!) {
          node(id: $id) {
            ... on Issue {
              id
            }
          }
        }
        """,
        {"id": issue["node_id"]},
    )["node"]["id"]

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
        {"project": PROJECT_ID, "content": node_id},
    )["addProjectV2ItemById"]["item"]["id"]

    # 5. Felder setzen
    for name, value in {
        "Start": start,
        "End": end,
    }.items():
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
                projectV2Item {
                  id
                }
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
            projectV2Item {
              id
            }
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

    print(f"Synced: {title}")
