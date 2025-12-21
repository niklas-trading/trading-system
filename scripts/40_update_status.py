import os
from datetime import date
from lib.github import graphql
from lib.config import PLAN_LABEL, WEEK_LABEL

ORG = os.environ["ORG"]
REPO = os.environ["REPO"]
PROJECT_NUMBER = int(os.environ["PROJECT_NUMBER"])

today = date.today()

# ---- Project laden
data = graphql(
    """
    query($org: String!, $number: Int!) {
      organization(login: $org) {
        projectV2(number: $number) {
          id
          items(first: 100) {
            nodes {
              id
              content {
                ... on Issue {
                  title
                  labels(first: 10) { nodes { name } }
                }
              }
              fieldValues(first: 20) {
                nodes {
                  ... on ProjectV2ItemFieldDateValue {
                    date
                    field { name }
                  }
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    field { name }
                  }
                }
              }
            }
          }
          fields(first: 20) {
            nodes {
              ... on ProjectV2SingleSelectField {
                id
                name
                options { id name }
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

status_field = next(
    f for f in project["fields"]["nodes"] if f["name"] == "Status"
)
status_options = {o["name"]: o["id"] for o in status_field["options"]}

def set_status(item_id, status):
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
            "field": status_field["id"],
            "option": status_options[status],
        },
    )

# ---- Status berechnen
for item in project["items"]["nodes"]:
    labels = {l["name"] for l in item["content"]["labels"]["nodes"]}
    if not {PLAN_LABEL, WEEK_LABEL}.issubset(labels):
        continue

    start = end = status = None

    for fv in item["fieldValues"]["nodes"]:
        if fv["field"]["name"] == "Start":
            start = fv["date"]
        elif fv["field"]["name"] == "End":
            end = fv["date"]
        elif fv["field"]["name"] == "Status":
            status = fv["name"]

    if status == "In Progress":
        continue

    if end and end < today.isoformat():
        set_status(item["id"], "Done")
    elif start and start <= today.isoformat() <= end:
        set_status(item["id"], "This Week")
    else:
        set_status(item["id"], "Backlog")

    print(f"✔ Status updated: {item['content']['title']}")
