"""ARTICLE_CODING.md -> LaTeX builder (arxiv-style preprint), the agentic
continuation paper. Mirrors scripts/build_paper_tex.py exactly (same
preamble packages, unicode map, theorem envs, conversion pipeline, and
unsrtnat bibliography), changing only the source file, the output
directory, and the title/author block.

Usage:
    python -m scripts.build_coding_tex
    cd paper_coding && pdflatex paper.tex && bibtex paper && \
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

SRC = REPO / "ARTICLE_CODING.md"
OUT_DIR = REPO / "paper_coding"
OUT_TEX = OUT_DIR / "paper.tex"
OUT_BIB = OUT_DIR / "refs.bib"
OUT_FIGS = OUT_DIR / "figures"

# Reuse the parent preamble up to the title block (packages, unicode map,
# theorem environments), then append the agentic paper's own title/author.
_PREAMBLE_HEAD = bpt.PREAMBLE.split("% --- title block")[0]

_TITLE_BLOCK = r"""% --- title block ----------------------------------------------------------
\title{Memory Policy and Persistent Redirection in Agentic Coding Loops\\[2pt]
       \large\itshape Survival, compliance, and the laundering of injected\\
       \large\itshape instructions by context compaction}

\renewcommand{\shorttitle}{Memory policy and persistent redirection in agentic coding loops}

\author{Pawel Kaplanski~\orcidlink{0000-0003-2223-0870}\\{}Kaplanski AI Lab\\\texttt{pawel@kaplanski.ai}}
\date{\today}

\hypersetup{
  pdftitle={Memory Policy and Persistent Redirection in Agentic Coding Loops},
  pdfsubject={cs.AI, cs.LG, cs.CR},
  pdfauthor={Pawel Kaplanski},
  pdfkeywords={agentic LLM loops, indirect prompt injection, context
    compaction, memory policy, durable redirection, prompt-injection
    laundering, coding agents},
}

\begin{document}
\maketitle

\keywords{agentic LLM loops \and indirect prompt injection
  \and context compaction \and memory policy \and durable redirection
  \and prompt-injection laundering}

"""

PREAMBLE = _PREAMBLE_HEAD + _TITLE_BLOCK

# \nocite{*} guarantees the full verified reference list renders even where
# the author-year auto-linker can't disambiguate (e.g. two Yao-2023 papers,
# ReAct and Tree of Thoughts, which share first author and year).
POSTAMBLE = r"""

\nocite{*}
\bibliographystyle{unsrtnat}
\bibliography{refs}

\end{document}
"""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FIGS.mkdir(parents=True, exist_ok=True)

    article_text = SRC.read_text(encoding="utf-8")

    # Strip ## Abstract section and stash it (emit as \begin{abstract}).
    abstract_m = re.search(r"##\s*Abstract\s*\n([\s\S]*?)(?=\n##\s)", article_text)
    abstract_body = abstract_m.group(1).strip() if abstract_m else ""
    # Strip any trailing/embedded markdown horizontal rules captured with
    # the abstract (the capture runs up to the next "##", pulling in the
    # "---" separator). A literal "---" otherwise renders as an em-dash.
    abstract_body = re.sub(r"(?m)^---\s*$", "", abstract_body).strip()
    if abstract_m:
        article_text = article_text[:abstract_m.start()] + article_text[abstract_m.end():]

    article_text, refs = bpt._parse_references_section(article_text)

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

    # Remove the §N References section from the body
    article_text = re.sub(r"##\s*\d+\.\s*References[\s\S]*?(?=\n##\s|\Z)", "", article_text)

    # Remove the top-level "# Title" line and (if present) a following
    # "## " line. The italic continuation note becomes a lead paragraph.
    article_text = re.sub(r"\A#\s+[^\n]+\n", "", article_text)

    article_text, math_blocks = bpt._convert_math_blocks(article_text)
    article_text, code_blocks = bpt._convert_fenced_code(article_text)
    article_text = bpt._convert_figures(article_text, OUT_FIGS)
    article_text = bpt._convert_footnotes(article_text)
    article_text = bpt._convert_inline_code(article_text)
    article_text = bpt._convert_inline_emphasis(article_text)
    article_text = bpt._convert_links(article_text)
    article_text = bpt._replace_inline_citations(article_text, refs)
    article_text = bpt._replace_authoryear_citations(article_text, refs)
    article_text = bpt._convert_tables(article_text)
    article_text = bpt._convert_lists(article_text)
    article_text = bpt._convert_headings(article_text)
    article_text = bpt._convert_theorem_envs(article_text)
    article_text = bpt._escape_prose_specials(article_text)
    article_text = bpt._restore_fenced_code(article_text, code_blocks)
    article_text = bpt._restore_math_blocks(article_text, math_blocks)
    article_text = re.sub(r"^---\s*$", "", article_text, flags=re.MULTILINE)

    tex = (PREAMBLE
           + r"\begin{abstract}" + "\n"
           + abstract_body + "\n"
           + r"\end{abstract}" + "\n\n"
           + article_text + "\n"
           + POSTAMBLE)
    OUT_TEX.write_text(tex, encoding="utf-8")
    print(f"wrote {OUT_TEX} ({len(tex):,} chars)")

    OUT_BIB.write_text("\n".join(refs.values()), encoding="utf-8")
    print(f"wrote {OUT_BIB} ({len(refs)} BibTeX entries)")

    print("\nBuild:")
    print(f"  cd {OUT_DIR.relative_to(REPO)}")
    print("  pdflatex paper.tex && bibtex paper && pdflatex paper.tex && pdflatex paper.tex")
    return 0


if __name__ == "__main__":
    sys.exit(main())
