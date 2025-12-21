import re
from lib.github import rest
from lib.config import PLAN_LABEL, WEEK_LABEL
import os

ORG = os.environ["ORG"]
REPO = os.environ["REPO"]

def week_of(title):
    m = re.search(r"Woche\s+(\d+)", title)
    return int(m.group(1)) if m else None

issues = rest(
    "GET",
    f"https://api.github.com/repos/{ORG}/{REPO}/issues",
    params={"labels": f"{WEEK_LABEL},{PLAN_LABEL}", "state": "open"},
)

by_week = {}
for i in issues:
    w = week_of(i["title"])
    if w:
        by_week.setdefault(w, []).append(i)

for w, group in by_week.items():
    if len(group) > 1:
        group.sort(key=lambda x: x["created_at"], reverse=True)
        for old in group[1:]:
            print(f"Closing duplicate Woche {w}: #{old['number']}")
            rest(
                "PATCH",
                f"https://api.github.com/repos/{ORG}/{REPO}/issues/{old['number']}",
                json={"state": "closed"},
            )
