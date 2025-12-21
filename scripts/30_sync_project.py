import os
import re
import time
from lib.github import rest, graphql
from lib.plan import parse_plan
from lib.config import PLAN_LABEL, WEEK_LABEL

ORG = os.environ["ORG"]
REPO = os.environ["REPO"]
PROJECT_NUMBER = int(os.environ["PROJECT_NUMBER"])

def extract_week(title):
    m = re.search(r"Woche\s+(\d+)", title)
    return int(m.group(1)) if m else None

# ---- Project laden
data = graphql(
    """
    query($org: String!, $number: Int!) {
      organization(login: $org) {
        projectV2(number: $number) {
          id
          fields(first: 50) {
            nodes {
              ... on ProjectV2Field { id name }
              ... on ProjectV2SingleSelectField { id name }
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
    raise RuntimeError("Project not found")

PROJECT_ID = project["id"]

field_ids = {
    f["name"]: f["id"]
    for f in project["fields"]["nodes"]
    if f["name"] in ("Start", "End")
}

# ---- Issues holen
issues = rest(
    "GET",
    f"https://api.github.com/repos/{ORG}/{REPO}/issues",
    params={"state": "open", "labels": f"{WEEK_LABEL},{PLAN_LABEL}"},
)

issues_by_week = {
    extract_week(i["title"]): i
    for i in issues
    if extract_week(i["title"])
}

# ---- Plan laden
weeks = parse_plan()

def add_to_project(content_id, retries=5):
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

# ---- Sync
for w in weeks:
    issue = issues_by_week.get(w["week"])
    if not issue:
        continue

    item_id = add_to_project(issue["node_id"])

    for field, value in {
        "Start": w["start"].isoformat(),
        "End": w["end"].isoformat(),
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
              ) { projectV2Item { id } }
            }
            """,
            {
                "project": PROJECT_ID,
                "item": item_id,
                "field": field_ids[field],
                "value": value,
            },
        )

    print(f"✔ Project synced: Woche {w['week']}")
