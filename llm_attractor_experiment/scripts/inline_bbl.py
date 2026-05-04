"""
Produce an arXiv-submission-ready, self-contained paper.tex by inlining
the bibliography from paper.bbl.

Why this exists: the Kourgeorge arxiv-style README warns that arXiv's
TeX Live environment does NOT run BibTeX during compile. A submission
that contains `\\bibliography{refs}` + a separate `refs.bib` will fail
to produce a bibliography on the arXiv side. The standard workaround is
to run BibTeX locally, take the resulting `.bbl` (which is already a
ready-to-render `\\begin{thebibliography}...\\end{thebibliography}`
block), and paste it directly into the .tex file in place of the
`\\bibliography{}` line.

Pipeline:
  1. Read paper/paper.tex (rebuildable artifact from build_paper_tex.py).
  2. Read paper/paper.bbl (must exist — run `bibtex paper` first).
  3. Comment out `\\bibliographystyle{unsrtnat}` (irrelevant for inline).
  4. Replace `\\bibliography{refs}` with the literal .bbl contents.
  5. Write paper/paper_arxiv.tex (separate file — leaves the
     bibtex-driven paper.tex intact for local rebuilds).

Optional: with `--bundle`, also zip paper_arxiv.tex + arxiv.sty +
figures/ into paper/arxiv_submission.zip ready to upload.

Usage:
    # After build_paper_tex + close_theorem_envs + pdflatex + bibtex:
    python -m scripts.inline_bbl

    # And bundle the submission package:
    python -m scripts.inline_bbl --bundle

The result `paper_arxiv.tex` compiles with just `pdflatex` (no bibtex
pass needed) — that's what arXiv runs.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAPER_DIR = REPO / "paper"
TEX_PATH = PAPER_DIR / "paper.tex"
BBL_PATH = PAPER_DIR / "paper.bbl"
OUT_TEX = PAPER_DIR / "paper_arxiv.tex"
OUT_ZIP = PAPER_DIR / "arxiv_submission.zip"


def _inline(tex: str, bbl: str) -> str:
    """Splice .bbl content into .tex at the \\bibliography{} site."""
    out_lines: list[str] = []
    replaced_bib = False
    commented_style = False
    for line in tex.split("\n"):
        stripped = line.strip()
        if stripped.startswith(r"\bibliographystyle{") and not commented_style:
            out_lines.append("% " + line + "  % inlined for arXiv submission")
            commented_style = True
            continue
        if stripped.startswith(r"\bibliography{") and not replaced_bib:
            out_lines.append(
                "% " + line + "  % inlined for arXiv submission"
            )
            out_lines.append("")
            out_lines.append(bbl.rstrip())
            replaced_bib = True
            continue
        out_lines.append(line)
    if not replaced_bib:
        raise RuntimeError(
            r"\bibliography{...} not found in paper.tex — has it already "
            "been inlined? Or did build_paper_tex change its postamble?"
        )
    return "\n".join(out_lines)


def _bundle(extra_files: list[Path]) -> None:
    """Zip paper_arxiv.tex + arxiv.sty + figures/ + extras for upload."""
    arxiv_sty = PAPER_DIR / "arxiv.sty"
    figures_dir = PAPER_DIR / "figures"
    if not arxiv_sty.exists():
        raise RuntimeError(f"missing {arxiv_sty} — required for the bundle")
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(OUT_TEX, arcname="paper.tex")
        z.write(arxiv_sty, arcname="arxiv.sty")
        if figures_dir.exists():
            for fig in sorted(figures_dir.glob("*")):
                if fig.is_file():
                    z.write(fig, arcname=f"figures/{fig.name}")
        for extra in extra_files:
            if extra.exists():
                z.write(extra, arcname=extra.name)
    n_entries = sum(1 for _ in zipfile.ZipFile(OUT_ZIP).namelist())
    size_kb = OUT_ZIP.stat().st_size / 1024
    print(f"wrote {OUT_ZIP} ({n_entries} files, {size_kb:.0f} KB)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--bundle", action="store_true",
        help="also zip paper_arxiv.tex + arxiv.sty + figures/ into "
             "arxiv_submission.zip for direct upload",
    )
    args = ap.parse_args()

    if not TEX_PATH.exists():
        print(f"error: {TEX_PATH} not found — run build_paper_tex first")
        return 1
    if not BBL_PATH.exists():
        print(f"error: {BBL_PATH} not found — run `bibtex paper` first")
        return 1

    tex = TEX_PATH.read_text(encoding="utf-8")
    bbl = BBL_PATH.read_text(encoding="utf-8")
    inlined = _inline(tex, bbl)
    OUT_TEX.write_text(inlined, encoding="utf-8")
    n_bib_entries = bbl.count(r"\bibitem")
    print(f"wrote {OUT_TEX} ({len(inlined):,} chars, {n_bib_entries} bib entries inlined)")

    if args.bundle:
        _bundle(extra_files=[])
        print()
        print("Submission bundle ready. Upload arxiv_submission.zip to arXiv,")
        print("or extract its contents and upload the files individually.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
