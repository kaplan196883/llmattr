"""Extract figures with their surrounding subsection context for GPT-5.5
vision-plus-context analysis. Output a JSON inventory."""
import json
import re
from pathlib import Path

ARTICLE = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\ARTICLE.md")
OUT = Path(r"D:\ROOT\llmattr\llm_attractor_experiment\.dev\round23_figure_inventory.json")

text = ARTICLE.read_text(encoding="utf-8")
lines = text.split("\n")

# Pre-compute subsection boundaries: for each line index, which ## or ### heading
# does it belong to?
subsec_starts = []  # list of (line_idx, heading_text, level)
for i, line in enumerate(lines):
    m = re.match(r"^(#{2,3})\s+(.+)$", line)
    if m:
        subsec_starts.append((i, m.group(2), len(m.group(1))))

def find_subsection(line_idx: int) -> tuple[str, int, int]:
    """Find the deepest subsection containing line_idx; return (heading, start_line, end_line)."""
    # Find the last ### heading at or before line_idx
    last_section = None
    last_subsection = None
    for s_idx, heading, level in subsec_starts:
        if s_idx > line_idx:
            break
        if level == 2:
            last_section = (s_idx, heading, level)
            last_subsection = None  # reset
        elif level == 3:
            last_subsection = (s_idx, heading, level)
    # Prefer subsection; fall back to section
    chosen = last_subsection or last_section
    if chosen is None:
        return ("(top)", 0, len(lines))
    s_idx, heading, level = chosen
    # End is the next heading at the same or higher level
    end_idx = len(lines)
    for ns_idx, _, n_level in subsec_starts:
        if ns_idx > s_idx and n_level <= level:
            end_idx = ns_idx
            break
    return (heading, s_idx, end_idx)


# Match figure blocks with multi-line caption
pat = re.compile(
    r"!\[(Fig|ED Fig)\s+(\d+)\.\s+\*\*(.+?)\.\*\*\s+(.+?)\]\(([^)]+\.png)\)",
    re.DOTALL,
)

figures = []
for m in pat.finditer(text):
    # Find the line number where this figure block starts
    start_pos = m.start()
    line_idx = text[:start_pos].count("\n")

    label_class = m.group(1)
    num = int(m.group(2))
    title = m.group(3).rstrip(".").strip()
    caption_body = m.group(4).strip()
    path = m.group(5)

    heading, sec_start, sec_end = find_subsection(line_idx)
    # Strip the figure block(s) from context to keep just prose/tables
    section_text = "\n".join(lines[sec_start:sec_end])
    section_text_clean = pat.sub("[FIGURE BLOCK ELIDED]", section_text)
    # Trim to avoid huge contexts (max ~6000 chars)
    if len(section_text_clean) > 6000:
        section_text_clean = section_text_clean[:6000] + "\n...[truncated]"

    fig_id = f"{label_class.replace(' ', '')}{num}"  # e.g. "Fig1" or "EDFig1"
    figures.append({
        "id": fig_id,
        "label_class": label_class,
        "num": num,
        "title": title,
        "caption_body": caption_body,
        "source_path": path,
        "abs_path": str((Path(r"D:\ROOT\llmattr\llm_attractor_experiment") / path).resolve()),
        "subsection_heading": heading,
        "subsection_text": section_text_clean,
    })

OUT.write_text(json.dumps(figures, indent=2), encoding="utf-8")
print(f"extracted {len(figures)} figures")
for f in figures:
    short_path = f['source_path'][-60:]
    print(f"  {f['id']:10s} sec={f['subsection_heading'][:35]:36s}  -> ...{short_path}")
