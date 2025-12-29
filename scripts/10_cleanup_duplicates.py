import os
import re
from lib.github import rest
from lib.config import PLAN_LABEL, WEEK_LABEL

ORG = os.environ["ORG"]
REPO = os.environ["REPO"]

PLAN_ID_RE = re.compile(r"<!--\s*plan-id:\s*([A-Za-z0-9_-]+)\s*-->")

def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss")
    s = re.sub(r"[^a-z0-9\s\-_]+", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "week"

def extract_plan_id(issue):
    body = issue.get("body") or ""
    m = PLAN_ID_RE.search(body)
    if m:
        return m.group(1)
    title = issue.get("title") or ""
    parts = re.split(r"\s+[–-]\s+", title.strip(), maxsplit=1)
    suffix = parts[1] if len(parts) == 2 else title
    return _slugify(suffix)

def list_open_plan_issues():
    issues = []
    page = 1
    while True:
        batch = rest(
            "GET",
            f"https://api.github.com/repos/{ORG}/{REPO}/issues",
            params={"labels": f"{WEEK_LABEL},{PLAN_LABEL}", "state": "open", "per_page": 100, "page": page},
        )
        if not batch:
            break
        issues.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return issues

issues = list_open_plan_issues()

by_pid = {}
for i in issues:
    pid = extract_plan_id(i)
    by_pid.setdefault(pid, []).append(i)

closed = 0
for pid, group in by_pid.items():
    if len(group) <= 1:
        continue
    group.sort(key=lambda x: x["created_at"], reverse=True)
    for old in group[1:]:
        print(f"Closing duplicate plan-id {pid}: #{old['number']}")
        rest("PATCH", f"https://api.github.com/repos/{ORG}/{REPO}/issues/{old['number']}", json={"state": "closed"})
        closed += 1

print(f"✔ Duplicate cleanup done (closed={closed})")
