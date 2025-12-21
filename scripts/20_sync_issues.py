from lib.github import rest
from lib.plan import parse_plan
from lib.config import PLAN_LABEL, WEEK_LABEL
import os

ORG = os.environ["ORG"]
REPO = os.environ["REPO"]

# ---------------------------------------------
# Plan laden
# ---------------------------------------------

weeks = parse_plan()

# ---------------------------------------------
# Bestehende Issues holen (nur plan-2026)
# ---------------------------------------------

existing = rest(
    "GET",
    f"https://api.github.com/repos/{ORG}/{REPO}/issues",
    params={
        "state": "open",
        "labels": PLAN_LABEL,
        "per_page": 100,
    },
)

# Index: week-XX -> Issue
by_week_label = {}

for issue in existing:
    labels = {l["name"] for l in issue["labels"]}
    for l in labels:
        if l.startswith("week-"):
            by_week_label[l] = issue

# ---------------------------------------------
# Upsert pro Woche
# ---------------------------------------------

for w in weeks:
    week_label = f"week-{w['week']:02d}"
    labels = [PLAN_LABEL, WEEK_LABEL, week_label]

    if week_label in by_week_label:
        issue = by_week_label[week_label]

        # Titel / Body aktualisieren (idempotent)
        if issue["title"] != w["title"] or issue["body"] != w["body"]:
            rest(
                "PATCH",
                issue["url"],
                json={
                    "title": w["title"],
                    "body": w["body"],
                },
            )
            print(f"Updated issue for {week_label}")
        else:
            print(f"No change for {week_label}")

    else:
        # Issue existiert sicher nicht → neu anlegen
        rest(
            "POST",
            f"https://api.github.com/repos/{ORG}/{REPO}/issues",
            json={
                "title": w["title"],
                "body": w["body"],
                "labels": labels,
            },
        )
        print(f"Created issue for {week_label}")

print("✔ Issues synced (strict, duplicate-safe)")
