"""Compare before/after screenshots produced by capture_screens.mjs."""
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageChops

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "_desktop_artifacts")
BEFORE = sys.argv[2] if len(sys.argv) > 2 else "before_mobile"
AFTER = sys.argv[3] if len(sys.argv) > 3 else "after_mobile"

before = json.loads((OUT / f"capture_{BEFORE}.json").read_text(encoding="utf-8"))
after = {((e["engine"], e["width"], e["page"])): e for e in json.loads((OUT / f"capture_{AFTER}.json").read_text(encoding="utf-8"))}

rows = []
for item in before:
    key = (item["engine"], item["width"], item["page"])
    other = after.get(key)
    if not other or item.get("error") or other.get("error"):
        rows.append({**key, "status": "missing", "diff": None})
        continue
    a = Image.open(item["file"]).convert("RGB")
    b = Image.open(other["file"]).convert("RGB")
    if a.size != b.size:
        rows.append({**key, "status": "size-mismatch", "diff": None})
        continue
    diff = ImageChops.difference(a, b)
    bbox = diff.getbbox()
    changed = sum(1 for px in diff.getdata() if px != (0, 0, 0))
    total = a.size[0] * a.size[1]
    rows.append({
        "engine": item["engine"], "width": item["width"], "page": item["page"],
        "status": "identical" if bbox is None else "changed",
        "changed_pixels": changed,
        "changed_ratio": round(changed / total, 6),
        "bbox": list(bbox) if bbox else None
    })

summary = {
    "before": BEFORE, "after": AFTER, "compared": len(rows),
    "identical": sum(1 for r in rows if r["status"] == "identical"),
    "changed": sum(1 for r in rows if r["status"] == "changed"),
    "problems": sum(1 for r in rows if r["status"] not in ("identical", "changed")),
    "max_changed_ratio": max((r["changed_ratio"] or 0) for r in rows),
    "rows": rows
}
(OUT / f"compare_{BEFORE}_{AFTER}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2, ensure_ascii=False))
for row in rows:
    if row["status"] != "identical":
        print(row["width"], row["page"], row["status"], row.get("changed_ratio"))
