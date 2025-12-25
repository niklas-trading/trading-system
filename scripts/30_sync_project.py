import os
import re
import time
from lib.github import rest, graphql
from lib.plan import parse_plan, infer_plan_id_from_title
from lib.config import PLAN_LABEL, WEEK_LABEL

ORG = os.environ["ORG"]
REPO = os.environ["REPO"]
PROJECT_NUMBER = int(os.environ["PROJECT_NUMBER"])

PLAN_ID_RE = re.compile(r"<!--\s*plan-id:\s*([A-Za-z0-9_-]+)\s*-->")

def extract_plan_id(issue):
    body = issue.get("body") or ""
    m = PLAN_ID_RE.search(body)
    if m:
        return m.group(1)
    return infer_plan_id_from_title(issue.get("title") or "")

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
field_ids = {f["name"]: f["id"] for f in project["fields"]["nodes"] if f["name"] in ("Start", "End")}

issues = []
page = 1
while True:
    batch = rest(
        "GET",
        f"https://api.github.com/repos/{ORG}/{REPO}/issues",
        params={"state": "open", "labels": f"{WEEK_LABEL},{PLAN_LABEL}", "per_page": 100, "page": page},
    )
    if not batch:
        break
    issues.extend(batch)
    if len(batch) < 100:
        break
    page += 1

issues_by_pid = {}
for i in issues:
    pid = extract_plan_id(i)
    if pid in issues_by_pid:
        if i.get("created_at", "") > issues_by_pid[pid].get("created_at", ""):
            issues_by_pid[pid] = i
    else:
        issues_by_pid[pid] = i

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

for w in weeks:
    pid = w["id"]
    issue = issues_by_pid.get(pid)
    if not issue:
        continue

    item_id = add_to_project(issue["node_id"])

    for field, value in {"Start": w["start"].isoformat(), "End": w["end"].isoformat()}.items():
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
            {"project": PROJECT_ID, "item": item_id, "field": field_ids[field], "value": value},
        )

    print(f"✔ Project synced: plan-id={pid} (Woche {w['week']})")
