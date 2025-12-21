import os
import re
import time
import requests
from datetime import datetime, date

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

# -------------------------------------------------
# Helpers
# -------------------------------------------------

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

def extract_week_number(title: str):
    m = re.search(r"Woche\s+(\d+)", title)
    return int(m.group(1)) if m else None

def extract_week_title(block: str):
    return block.splitlines()[0].replace("## ", "").strip()

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

# -------------------------------------------------
# 0. CLEANUP: Deduplication nach Wochennummer
# -------------------------------------------------

print("Running cleanup of duplicate week issues...")

all_open = get_all_week_issues("open")
by_week = {}

for issue in all_open:
    week = extract_week_number(issue["title"])
    if week:
        by_week.setdefault(week, []).append(issue)

for week, issues in by_week.items():
    if len(issues) > 1:
        issues.sort(key=lambda i: i["created_at"], reverse=True)
        for old in issues[1:]:
            print(f"Closing duplicate week {week}: #{old['number']}")
            requests.patch(
                f"https://api.github.com/repos/{ORG}/{REPO}/issues/{old['number']}",
                headers=REST_HEADERS,
                json={"state": "closed"},
            )

# Refresh after cleanup
existing_issues = {
    extract_week_number(i["title"]): i
    for i in get_all_week_issues("open")
    if extract_week_number(i["title"])
}

# -------------------------------------------------
# 1. Project laden
# -------------------------------------------------

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
    raise RuntimeError("Project not found.")

PROJECT_ID = project["id"]

field_ids = {}
status_options = {}

for f in project["fields"]["nodes"]:
    if f["name"] in ("Start", "End", "Status"):
        field_ids[f["name"]] = f["id"]
        if f["name"] == "Status":
            for opt in f["options"]:
                status_options[opt["name"]] = opt["id"]

required = {"Start", "End", "Status"}
if not required.issubset(field_ids):
    raise RuntimeError(f"Missing fields: {required - field_ids.keys()}")

# -------------------------------------------------
# 2. Year Plan parsen
# -------------------------------------------------

with open("docs/year-plan.md", encoding="utf-8") as f:
    text = f.read()

weeks = re.split(r"(?=## Woche \d+)", text)

today = date.today()
current_week = today.isocalendar().week

# -------------------------------------------------
# 3. Project helpers
# -------------------------------------------------

def add_to_project_with_retry(content_id, retries=6):
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
                {"project": PROJECT_ID, "content": content_id},
            )["addProjectV2ItemById"]["item"]["id"]
        except RuntimeError:
            if i == retries - 1:
                raise
            time.sleep(1 + i)

def set_status(item_id, status_name):
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
            "option": status_options[status_name],
        },
    )

# -------------------------------------------------
# 4. Sync
# -------------------------------------------------

for block in weeks:
    if not block.startswith("## Woche"):
        continue

    raw_title = extract_week_title(block)
    week = extract_week_number(raw_title)
    if not week:
        continue

    canonical_title = raw_title  # already normalized by year-plan

    m = re.search(r"\*\*Zeitraum:\*\*\s*([0-9.]+)\s*[–-]\s*([0-9.]+)", block)
    if not m:
        continue

    start = datetime.strptime(m.group(1), "%d.%m.%Y").date().isoformat()
    end = datetime.strptime(m.group(2), "%d.%m.%Y").date().isoformat()

    # Issue holen oder erstellen
    if week in existing_issues:
        issue = existing_issues[week]
        if issue["title"] != canonical_title:
            requests.patch(
                f"https://api.github.com/repos/{ORG}/{REPO}/issues/{issue['number']}",
                headers=REST_HEADERS,
                json={"title": canonical_title},
            )
    else:
        issue = requests.post(
            f"https://api.github.com/repos/{ORG}/{REPO}/issues",
            headers=REST_HEADERS,
            json={"title": canonical_title, "body": block, "labels": ["week"]},
        ).json()

    content_id = issue["node_id"]
    item_id = add_to_project_with_retry(content_id)

    # Dates setzen
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

    # Automatischer Status
    if issue.get("state") == "open":
        if week < current_week:
            set_status(item_id, "Done")
        elif week == current_week:
            set_status(item_id, "This Week")
        else:
            set_status(item_id, "Backlog")

    print(f"✔ Synced Woche {week}")

print("✔ Full sync finished successfully.")
