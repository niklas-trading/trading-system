import re
import os
import requests

TOKEN = os.environ["GH_TOKEN"]
REPO = os.environ["REPO"]
PROJECT_ID = os.environ["PROJECT_ID"]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

with open("docs/year-plan.md", "r", encoding="utf-8") as f:
    text = f.read()

weeks = re.split(r"(?=## Woche \d+)", text)

for block in weeks:
    if not block.startswith("## Woche"):
        continue

    title_line = block.splitlines()[0].replace("## ", "").strip()
    week_nr = re.search(r"Woche (\d+)", title_line).group(1)

    date_match = re.search(r"\*\*Zeitraum:\*\* ([0-9.\-– ]+)", block)
    if not date_match:
        continue

    dates = date_match.group(1)

    issue_title = f"{title_line} ({dates})"

    # Create issue
    resp = requests.post(
        f"https://api.github.com/repos/{REPO}/issues",
        headers=HEADERS,
        json={
            "title": issue_title,
            "body": block,
            "labels": ["week"]
        }
    )

    print(f"Created issue for week {week_nr}")
