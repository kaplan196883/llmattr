"""Build the MERGED v2 paper for arXiv:2605.02236 replacement.

arXiv moderation declined the standalone agentic submission and invited
incorporating it into the parent paper as a replacement. This builder
combines the parent (ARTICLE.md, the text-loop study) and the agentic
continuation (ARTICLE_CODING.md) into one document, structured as two
PARTS so that each part keeps its own section numbering. This is
essential because both papers cite their own sections literally in prose
("Supplementary §12.4", "§5.9 (AC3)"); renumbering would break those
references. A `\\setcounter{section}{0}` at the start of Part II resets
the counter so the agentic part renders §1..§13 exactly as written.

Output: paper_merged/paper.tex + refs.bib + figures/ (+ arXiv zip).

Run:
    python -m scripts.build_merged_tex
    cd paper_merged && pdflatex paper.tex && bibtex paper && \
        pdflatex paper.tex && pdflatex paper.tex
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import build_paper_tex as bpt  # noqa: E402

PARENT_SRC = REPO / "ARTICLE.md"
AGENTIC_SRC = REPO / "ARTICLE_CODING.md"
OUT_DIR = REPO / "paper_merged"
OUT_TEX = OUT_DIR / "paper.tex"
OUT_BIB = OUT_DIR / "refs.bib"
OUT_FIGS = OUT_DIR / "figures"

# Preamble = parent preamble up to the title block, then a combined title.
_PREAMBLE_HEAD = bpt.PREAMBLE.split("% --- title block")[0]

_TITLE_BLOCK = r"""% --- title block ----------------------------------------------------------
\title{Perturbation Dose Responses in Recursive LLM Loops\\[2pt]
       \large\itshape Raw switching, stochastic floors, and persistent escape under\\
       \large\itshape append, replace, and dialog updates; with an agentic-coding-loop extension}

\renewcommand{\shorttitle}{Perturbation dose responses in recursive LLM loops}

\author{Pawel Kaplanski~\orcidlink{0000-0003-2223-0870}\\{}Kaplanski AI Lab\\\texttt{pawel@kaplanski.ai}}
\date{\today}

\hypersetup{
  pdftitle={Perturbation Dose Responses in Recursive LLM Loops},
  pdfsubject={cs.AI, cs.LG, cs.CL, cs.CR},
  pdfauthor={Pawel Kaplanski},
  pdfkeywords={recursive LLM loops, perturbation dose response, agentic
    coding loops, indirect prompt injection, context compaction, memory
    policy, basin switching},
}

\begin{document}
\maketitle

\keywords{recursive LLM loops \and perturbation dose response
  \and context-update rules \and agentic coding loops
  \and indirect prompt injection \and context compaction}

"""

PREAMBLE = _PREAMBLE_HEAD + _TITLE_BLOCK

POSTAMBLE = r"""

\bibliographystyle{unsrtnat}
\bibliography{refs}

\end{document}
"""

# A short bridge note introducing Part II, so the merge reads as one work.
PART2_HEADER = r"""

\clearpage
\part*{Part II: Agentic coding loops}
\addcontentsline{toc}{part}{Part II: Agentic coding loops}
% Reset section numbering so Part II renders \S1..\S13 as written, keeping
% its internal cross-references (e.g. "\S5.9") valid.
\setcounter{section}{0}
\renewcommand{\thesection}{\arabic{section}}

\noindent\emph{Part II extends the framework of Part I from free-form
text loops to agentic coding loops. It was prepared as a separate
manuscript and is incorporated here at the request of arXiv moderation;
section numbers below are local to Part II. Citations of ``the parent
paper'' refer to Part I.}

"""

PART1_HEADER = r"""
\part*{Part I: Recursive text loops}
\addcontentsline{toc}{part}{Part I: Recursive text loops}

"""


def _convert_body(text: str, refs: dict, abstract_pull: bool):
    """Run the parent conversion pipeline on one markdown body. Returns
    (converted_body, abstract_or_None). Mirrors build_paper_tex.main()
    ordering exactly."""
    # Strip stray HTML comments (e.g. "<!-- ... -->") that would otherwise
    # render verbatim in the PDF and carry en-dashes from their "--".
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    abstract_body = None
    if abstract_pull:
        m = re.search(r"##\s*Abstract\s*\n([\s\S]*?)(?=\n##\s)", text)
        if m:
            abstract_body = m.group(1).strip()
            abstract_body = re.sub(r"(?m)^---\s*$", "", abstract_body).strip()
            text = text[:m.start()] + text[m.end():]

    # Remove the §N References section from the body (emitted via BibTeX).
    text = re.sub(r"##\s*\d+\.\s*References[\s\S]*?(?=\n##\s|\Z)", "", text)
    # Drop the top-level "# Title" line and a following "## subtitle" line.
    text = re.sub(r"\A#\s+[^\n]+\n", "", text)
    text = re.sub(r"\A##\s+[^\n]+\n", "", text, count=1)

    if abstract_body:
        abstract_body, _am = bpt._convert_math_blocks(abstract_body)
        abstract_body, _ac = bpt._convert_fenced_code(abstract_body)
        abstract_body = bpt._convert_inline_code(abstract_body)
        abstract_body = bpt._convert_inline_emphasis(abstract_body)
        abstract_body = bpt._convert_links(abstract_body)
        abstract_body = bpt._replace_inline_citations(abstract_body, refs)
        abstract_body = bpt._replace_authoryear_citations(abstract_body, refs)
        abstract_body = bpt._escape_prose_specials(abstract_body)
        abstract_body = bpt._restore_fenced_code(abstract_body, _ac)
        abstract_body = bpt._restore_math_blocks(abstract_body, _am)

    text, math_blocks = bpt._convert_math_blocks(text)
    text, code_blocks = bpt._convert_fenced_code(text)
    text = bpt._convert_figures(text, OUT_FIGS)
    text = bpt._convert_footnotes(text)
    text = bpt._convert_inline_code(text)
    text = bpt._convert_inline_emphasis(text)
    text = bpt._convert_links(text)
    text = bpt._replace_inline_citations(text, refs)
    text = bpt._replace_authoryear_citations(text, refs)
    text = bpt._convert_tables(text)
    text = bpt._convert_lists(text)
    text = bpt._convert_headings(text)
    text = bpt._convert_theorem_envs(text)
    text = bpt._escape_prose_specials(text)
    text = bpt._restore_fenced_code(text, code_blocks)
    text = bpt._restore_math_blocks(text, math_blocks)
    text = re.sub(r"^---\s*$", "", text, flags=re.MULTILINE)
    # Defensive: strip stray control chars (arXiv pdflatex rejects them).
    text = "".join(c for c in text if c in "\n\t" or ord(c) >= 32)
    return text, abstract_body


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FIGS.mkdir(parents=True, exist_ok=True)

    parent_md = PARENT_SRC.read_text(encoding="utf-8")
    agentic_md = AGENTIC_SRC.read_text(encoding="utf-8")

    # Parse references from BOTH and merge (dedupe by bibkey).
    parent_md2, parent_refs = bpt._parse_references_section(parent_md)
    agentic_md2, agentic_refs = bpt._parse_references_section(agentic_md)
    refs = dict(parent_refs)
    added = 0
    for k, v in agentic_refs.items():
        if k not in refs:
            refs[k] = v
            added += 1
    print(f"references: {len(parent_refs)} parent + {added} new from agentic "
          f"= {len(refs)} merged")

    # Convert each body against the MERGED ref dict so cross-part citations
    # resolve. Pull the abstract only from the parent (Part I).
    parent_body, parent_abstract = _convert_body(parent_md2, refs, abstract_pull=True)
    agentic_body, _ = _convert_body(agentic_md2, refs, abstract_pull=False)

    # Figure fix-up. _convert_figures only copies a PNG (and emits a clean
    # figures/figNN.png include) when the data/ source still exists on disk;
    # several parent-paper sources have since been removed, leaving raw
    # data/... includegraphics paths. The canonical fig01..figNN.png were
    # built earlier into paper/figures/ from the SAME ordered sequence, so
    # we rewrite every includegraphics{...} in appearance order to
    # figures/figNN.png and copy the canonical PNGs across. Parent figures
    # come first (matching paper/figures/ numbering); the agentic body has
    # no inline figures, so no renumbering hazard.
    parent_figs_src = REPO / "paper" / "figures"
    _fig_counter = {"n": 0}

    def _renumber(m):
        _fig_counter["n"] += 1
        return (m.group(1) + "{figures/fig%02d.png}" % _fig_counter["n"])

    inc_pat = re.compile(r"(\\includegraphics(?:\[[^\]]*\])?)\{[^}]+\}")
    parent_body = inc_pat.sub(_renumber, parent_body)
    n_parent_figs = _fig_counter["n"]
    # Copy canonical PNGs (fig01..figNN) from the standalone parent build.
    copied = 0
    for i in range(1, n_parent_figs + 1):
        src = parent_figs_src / f"fig{i:02d}.png"
        if src.exists():
            shutil.copyfile(src, OUT_FIGS / f"fig{i:02d}.png")
            copied += 1
        else:
            print(f"  WARNING: missing canonical figure {src}")
    print(f"figures: rewrote {n_parent_figs} includegraphics, copied {copied} PNGs")

    tex = (
        PREAMBLE
        + r"\begin{abstract}" + "\n" + (parent_abstract or "") + "\n"
        + r"\end{abstract}" + "\n\n"
        + PART1_HEADER
        + parent_body + "\n"
        + PART2_HEADER
        + agentic_body + "\n"
        + POSTAMBLE
    )
    # final control-char guard on the whole document
    tex = "".join(c for c in tex if c in "\n\t" or ord(c) >= 32)

    OUT_TEX.write_text(tex, encoding="utf-8")
    print(f"wrote {OUT_TEX} ({len(tex):,} chars)")

    OUT_BIB.write_text("\n".join(refs.values()), encoding="utf-8")
    print(f"wrote {OUT_BIB} ({len(refs)} BibTeX entries)")

    n_figs = len(list(OUT_FIGS.glob("*.png")))
    print(f"figures in {OUT_FIGS}: {n_figs}")

    print("\nBuild:")
    print(f"  cd {OUT_DIR.relative_to(REPO)}")
    print("  pdflatex paper.tex && bibtex paper && pdflatex paper.tex && pdflatex paper.tex")
    return 0


if __name__ == "__main__":
    sys.exit(main())
