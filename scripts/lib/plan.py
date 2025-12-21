import re
from datetime import datetime

def parse_plan(path="docs/year-plan.md"):
    with open(path, encoding="utf-8") as f:
        text = f.read()

    blocks = re.split(r"(?=## Woche \d+)", text)
    weeks = []

    for block in blocks:
        if not block.startswith("## Woche"):
            continue

        title = block.splitlines()[0].replace("## ", "").strip()
        m = re.search(r"Woche\s+(\d+)", title)
        if not m:
            continue

        dates = re.search(
            r"\*\*Zeitraum:\*\*\s*([0-9.]+)\s*[–-]\s*([0-9.]+)", block
        )
        if not dates:
            continue

        weeks.append({
            "week": int(m.group(1)),
            "title": title,
            "body": block,
            "start": datetime.strptime(dates.group(1), "%d.%m.%Y").date(),
            "end": datetime.strptime(dates.group(2), "%d.%m.%Y").date(),
        })

    return weeks
