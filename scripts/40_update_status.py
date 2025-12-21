import os
from datetime import date
from lib.github import graphql
from lib.config import PLAN_LABEL, WEEK_LABEL

ORG = os.environ["ORG"]
PROJECT_NUMBER = int(os.environ["PROJECT_NUMBER"])
today = date.today().isoformat()

# -------------------------------------------------
# Project + Fields + Items laden (FIELD-ID BASIERT)
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
          items(first: 100) {
            nodes {
              id
              content {
                ... on Issue {
                  title
                  labels(first: 10) {
                    nodes { name }
                  }
                }
              }
              fieldValues(first: 20) {
                nodes {
                  __typename
                  ... on ProjectV2ItemFieldDateValue {
                    date
                    fieldId
                  }
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    optionId
                    fieldId
                  }
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

# -------------------------------------------------
# Feld-IDs auf Namen abbilden
# -------------------------------------------------

field_name_by_id = {}
status_field_id = None
status_option_by_id = {}

for f in project["fields"]["nodes"]:
    field_name_by_id[f["id"]] = f["name"]
    if f["name"] == "Status":
        status_field_id = f["id"]
        for opt in f["options"]:
            status_option_by_id[opt["id"]] = opt["name"]

def set_status(item_id, option_id):
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
            "field": status_field_id,
            "option": option_id,
        },
    )

# -------------------------------------------------
# Status-Logik (rein datumsgesteuert)
# -------------------------------------------------

for item in project["items"]["nodes"]:
    if not item["content"]:
        continue

    labels = {l["name"] for l in item["content"]["labels"]["nodes"]}
    if not {PLAN_LABEL, WEEK_LABEL}.issubset(labels):
        continue

    start = None
    end = None
    current_status = None
    current_status_option_id = None

    for fv in item["fieldValues"]["nodes"]:
        field_name = field_name_by_id.get(fv["fieldId"])

        if fv["__typename"] == "ProjectV2ItemFieldDateValue":
            if field_name == "Start":
                start = fv["date"]
            elif field_name == "End":
                end = fv["date"]

        elif fv["__typename"] == "ProjectV2ItemFieldSingleSelectValue":
            if field_name == "Status":
                current_status_option_id = fv["optionId"]
                current_status = status_option_by_id.get(fv["optionId"])

    # Manuelles In Progress respektieren
    if current_status == "In Progress":
        continue

    if end and end < today:
        target = "Done"
    elif start and start <= today <= end:
        target = "This Week"
    else:
        target = "Backlog"

    if current_status != target:
        option_id = next(
            oid for oid, name in status_option_by_id.items() if name == target
        )
        set_status(item["id"], option_id)
        print(f"✔ Status updated → {target}: {item['content']['title']}")
