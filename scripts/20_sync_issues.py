import os
import re
from lib.github import rest
from lib.plan import parse_plan, infer_plan_id_from_title
from lib.config import PLAN_LABEL, WEEK_LABEL

ORG = os.environ["ORG"]
REPO = os.environ["REPO"]

# Safety switch: only close removed plan items if explicitly enabled
CLOSE_REMOVED = os.environ.get("CLOSE_REMOVED", "false").lower() in ("1", "true", "yes")

WEEK_LABEL_RE = re.compile(r"^week-\d{2}$")
PLAN_ID_RE = re.compile(r"<!--\s*plan-id:\s*([A-Za-z0-9_-]+)\s*-->")

def extract_plan_id(issue):
    body = issue.get("body") or ""
    m = PLAN_ID_RE.search(body)
    if m:
        return m.group(1)
    return infer_plan_id_from_title(issue.get("title") or "")

def list_open_plan_issues():
    issues = []
    page = 1
    while True:
        batch = rest(
            "GET",
            f"https://api.github.com/repos/{ORG}/{REPO}/issues",
            params={"state": "open", "labels": PLAN_LABEL, "per_page": 100, "page": page},
        )
        if not batch:
            break
        issues.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return issues

def compute_labels(issue, desired_week_label):
    # Preserve non-week labels; enforce PLAN_LABEL, WEEK_LABEL and current week-XX
    existing_names = [l["name"] for l in (issue.get("labels") or []) if "name" in l]
    keep = [n for n in existing_names if not WEEK_LABEL_RE.match(n)]
    base = set(keep)
    base.add(PLAN_LABEL)
    base.add(WEEK_LABEL)
    base.add(desired_week_label)
    return sorted(base)

weeks = parse_plan()
plan_ids = {w["id"] for w in weeks}

existing = list_open_plan_issues()

# Index: plan-id -> Issue (defensive: keep newest if duplicates exist)
by_plan_id = {}
for issue in existing:
    pid = extract_plan_id(issue)
    if pid in by_plan_id:
        if issue.get("created_at", "") > by_plan_id[pid].get("created_at", ""):
            by_plan_id[pid] = issue
    else:
        by_plan_id[pid] = issue

created = updated = relabeled = closed = 0

for w in weeks:
    pid = w["id"]
    desired_week_label = f"week-{w['week']:02d}"

    if pid in by_plan_id:
        issue = by_plan_id[pid]
        patch = {}

        if issue.get("title") != w["title"]:
            patch["title"] = w["title"]
        if (issue.get("body") or "") != (w["body"] or ""):
            patch["body"] = w["body"]

        desired_labels = compute_labels(issue, desired_week_label)
        current_labels = sorted({l["name"] for l in (issue.get("labels") or []) if "name" in l})
        if desired_labels != current_labels:
            patch["labels"] = desired_labels
            relabeled += 1

        if patch:
            rest("PATCH", issue["url"], json=patch)
            updated += 1
            print(f"Updated issue for plan-id={pid} (week={w['week']})")
        else:
            print(f"No change for plan-id={pid} (week={w['week']})")
    else:
        rest(
            "POST",
            f"https://api.github.com/repos/{ORG}/{REPO}/issues",
            json={"title": w["title"], "body": w["body"], "labels": [PLAN_LABEL, WEEK_LABEL, desired_week_label]},
        )
        created += 1
        print(f"Created issue for plan-id={pid} (week={w['week']})")

if CLOSE_REMOVED:
    for pid, issue in by_plan_id.items():
        if pid not in plan_ids:
            print(f"Closing removed plan-id={pid}: #{issue['number']}")
            rest("PATCH", issue["url"], json={"state": "closed"})
            closed += 1

print(f"✔ Issues synced (migrationsafe). created={created}, updated={updated}, relabeled={relabeled}, closed={closed}")
