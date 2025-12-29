import re
import unicodedata
from datetime import datetime
from typing import Optional

_PLAN_ID_RE = re.compile(r"<!--\s*plan-id:\s*([A-Za-z0-9_-]+)\s*-->")

def slugify(text: str) -> str:
    """Create a stable-ish slug from human text (German friendly)."""
    text = text.strip().lower()
    text = (
        text.replace("ä", "ae")
            .replace("ö", "oe")
            .replace("ü", "ue")
            .replace("ß", "ss")
    )
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9\s\-_]+", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "week"

def extract_plan_id_from_text(text: str) -> Optional[str]:
    m = _PLAN_ID_RE.search(text or "")
    return m.group(1) if m else None

def infer_plan_id_from_title(title: str) -> str:
    """Infer plan-id from the title part after the dash (fallback)."""
    parts = re.split(r"\s+[–-]\s+", title.strip(), maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        return slugify(parts[1])
    return slugify(title)

def ensure_plan_id_in_block(block: str, plan_id: str) -> str:
    """Inject <!-- plan-id: ... --> right under the heading if missing."""
    if extract_plan_id_from_text(block):
        return block
    lines = block.splitlines()
    if not lines:
        return block
    lines.insert(1, f"<!-- plan-id: {plan_id} -->")
    return "\n".join(lines) + ("\n" if block.endswith("\n") else "")

def parse_plan(path: str = "docs/year-plan.md"):
    """Parse weekly plan markdown into structured items.

    Each item includes a stable 'id' (plan-id). If no explicit plan-id is present
    in the markdown block, it is inferred from the title and injected into the
    body returned (issues will then carry it).
    """
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
            r"\*\*Zeitraum:\*\*\s*([0-9.]+)\s*[–-]\s*([0-9.]+)",
            block,
        )
        if not dates:
            continue

        plan_id = extract_plan_id_from_text(block) or infer_plan_id_from_title(title)
        body = ensure_plan_id_in_block(block, plan_id)

        weeks.append({
            "id": plan_id,
            "week": int(m.group(1)),
            "title": title,
            "body": body,
            "start": datetime.strptime(dates.group(1), "%d.%m.%Y").date(),
            "end": datetime.strptime(dates.group(2), "%d.%m.%Y").date(),
        })

    return weeks
