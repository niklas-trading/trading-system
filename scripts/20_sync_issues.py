from lib.github import rest
from lib.plan import parse_plan
from lib.config import PLAN_LABEL, WEEK_LABEL
import os

ORG = os.environ["ORG"]
REPO = os.environ["REPO"]

weeks = parse_plan()

existing = rest(
    "GET",
    f"https://api.github.com/repos/{ORG}/{REPO}/issues",
    params={"labels": f"{WEEK_LABEL},{PLAN_LABEL}", "state": "open"},
)

by_week = {int(w["title"].split()[1]): w for w in existing}

for w in weeks:
    if w["week"] in by_week:
        issue = by_week[w["week"]]
        if issue["title"] != w["title"]:
            rest(
                "PATCH",
                issue["url"],
                json={"title": w["title"], "body": w["body"]},
            )
    else:
        rest(
            "POST",
            f"https://api.github.com/repos/{ORG}/{REPO}/issues",
            json={
                "title": w["title"],
                "body": w["body"],
                "labels": [WEEK_LABEL, PLAN_LABEL],
            },
        )

print("✔ Issues synced")
