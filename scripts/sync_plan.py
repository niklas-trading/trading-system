import os
import re
import time
import requests
from datetime import datetime

TOKEN = os.environ["GITHUB_TOKEN"]
ORG = os.environ["ORG"]
PROJECT_NUMBER = int(os.environ["PROJECT_NUMBER"])
REPO = os.environ["REPO"]

API_URL = "https://api.github.com/graphql"
REST_HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}
GRAPHQL_HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# -----------------------------
# Helpers
# -----------------------------

def graphql(query, variables=None):
    r = requests.post(
        API_URL,
        headers=GRAPHQL_HEADERS,
        json={"query": query, "variables": variables or {}},
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]

def get_all_week_issues(state="open"):
    issues = []
    page = 1
    while True:
        r = requests.get(
            f"https://api.github.com/repos/{ORG}/{REPO}/issues",
            headers=REST_HEADERS,
            params={
                "state": state,
                "labels": "week",
                "per_page": 100,
                "page": page,
            },
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        issues.extend(batch)
        page += 1
    return issues

# -----------------------------
# 0. CLEANUP: Duplicate Issues schließen
# -----------------------------

print("Running cleanup of duplicate week issues...")

all_issues = get_all_week_issues(state="open")

by_title = {}
for issue in all_issues:
    by_title.setdefault(issue["title"], []).append(issue)

for title, issues in by_title.items():
    if len(issues) > 1:
        # sort: newest first → keep newest
        issues.sort(key=lambda i: i["created_at"], reverse=True)
        for old in issues[1:]:
            print(f"Closing duplicate: {old['title']} #{old['number']}")
            requests.patch(
                f"https://api.github.com/repos/{ORG}/{REPO}/issues/{old['number']}",
                headers=REST_HEADERS,
                json={"state": "closed"},
            )

# Refresh open issues after cleanup
existing_issues = {i["title"]: i for i in get_all_week_issues(state="open")}

# -----------------------------
# 1. Project laden
# -----------------------------

data = graphql(
    """
    query($org: String!, $number: Int!) {
      organization(login: $org) {
        projectV2(number: $number) {
          id
          fields(first: 50) {
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
if not project:
    raise RuntimeError("Project not found. Check PROJECT_NUMBER and PAT permissions.")

PROJECT_ID = project["id"]

field_ids = {}
status_options = {}

for f in project["fields"]["nodes"]:
    if f["name"] in ("Start", "End", "Status"):
        field_ids[f["name"]] = f["id"]
        if f["name"] == "Status":
            for opt in f["options"]:
                status_options[opt["name"]] = opt["id"]

missing = {"Start", "End", "Status"} - field_ids.keys()
if missing:
    raise RuntimeError(f"Missing required project fields: {missing}")

# -----------------------------
# 2. Year Plan parsen
# -----------------------------

with open("docs/year-plan.md", encoding="utf-8") as f:
    text = f.read()

weeks = re.split(r"(?=## Woche \d+)", text)

# -----------------------------
# 3. Sync
# -----------------------------

def add_to_project_with_retry(project_id, content_id, retries=6):
    for i in range(retries):
        try:
            return graphql(
                """
                mutation($project: ID!, $content: ID!) {
                  addProjectV2ItemById(
                    input: { projectId: $project, contentId: $content }
                  ) {
                    item { id }
                  }
                }
                """,
                {"project": project_id, "content": content_id},
            )["addProjectV2ItemById"]["item"]["id"]
        except RuntimeError as e:
            if i == retries - 1:
                raise
            time.sleep(1 + i)

for block in weeks:
    if not block.startswith("## Woche"):
        continue

    title = block.splitlines()[0].replace("## ", "").strip()

    m = re.search(r"\*\*Zeitraum:\*\*\s*([0-9.]+)\s*[–-]\s*([0-9.]+)", block)
    if not m:
        continue

    start = datetime.strptime(m.group(1), "%d.%m.%Y").date().isoformat()
    end = datetime.strptime(m.group(2), "%d.%m.%Y").date().isoformat()

    # 3.1 Issue holen oder erstellen
    if title in existing_issues:
        issue = existing_issues[title]
    else:
        issue = requests.post(
            f"https://api.github.com/repos/{ORG}/{REPO}/issues",
            headers=REST_HEADERS,
            json={"title": title, "body": block, "labels": ["week"]},
        ).json()

    content_id = issue["node_id"]

    # 3.2 Ins Project
    item_id = add_to_project_with_retry(PROJECT_ID, content_id)

    # 3.3 Dates setzen
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

    # 3.4 Status = Backlog (nur initial)
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

    print(f"Synced: {title}")

print("✔ Sync completed successfully.")
