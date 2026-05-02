"""For each figure, gather: subsection text + any sibling CSV/JSON data
files in the same directory. Output a per-figure bundle JSON for round-25
deep-description generation."""
import json
import re
from pathlib import Path

ROOT = Path(r"D:\ROOT\llmattr\llm_attractor_experiment")
INV = ROOT / ".dev" / "round23_figure_inventory.json"
OUT = ROOT / ".dev" / "round25_data_bundles.json"

inv = json.loads(INV.read_text(encoding="utf-8"))

bundles = []
for f in inv:
    fig_path = Path(f["abs_path"])
    fig_dir = fig_path.parent
    # Find sibling data files (CSV, JSON, MD reports), excluding mp4/png
    siblings = []
    if fig_dir.exists():
        for p in sorted(fig_dir.iterdir()):
            if p.is_file() and p.suffix.lower() in (".csv", ".json", ".md"):
                # Read up to 4000 chars; skip giant files (>200kb)
                try:
                    if p.stat().st_size < 200_000:
                        body = p.read_text(encoding="utf-8", errors="replace")[:4000]
                        siblings.append({"name": p.name, "size": p.stat().st_size, "snippet": body})
                except Exception:
                    pass
    # Cap total sibling-snippet payload at 8000 chars per figure
    total = 0
    kept = []
    for s in siblings:
        if total + len(s["snippet"]) > 8000:
            break
        kept.append(s)
        total += len(s["snippet"])
    f["siblings"] = kept
    bundles.append(f)

OUT.write_text(json.dumps(bundles, indent=2), encoding="utf-8")
print(f"wrote {len(bundles)} bundles, total {OUT.stat().st_size:,} bytes")
for b in bundles:
    n_sib = len(b.get("siblings", []))
    print(f"  {b['id']:10s} siblings={n_sib}")
