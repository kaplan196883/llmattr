"""
ARTICLE.md → LaTeX builder (arxiv-style preprint format).

Reads `ARTICLE.md` and emits a self-contained LaTeX project under
`paper/`:

    paper/paper.tex         — main LaTeX source with arxiv-style preamble
    paper/refs.bib          — BibTeX bibliography extracted from §13
    paper/figures/*.png     — copied figure PNGs
    paper/README.md         — build instructions

Pipeline:

  1. Read ARTICLE.md.
  2. Extract title + abstract.
  3. Walk section tree (##, ###, ####). Translate markdown to LaTeX
     section commands.
  4. Translate inline patterns: bold, italic, code, math, links.
  5. Translate lists (- ... and 1. ...).
  6. Translate markdown tables to tabular environments.
  7. Walk `![Figure N. caption](path)` → \begin{figure} env, copy
     PNG to paper/figures/.
  8. Wrap Lemma 1 / Corollary 1 / Corollary 2 / Conjecture 1 in
     proper theorem environments via \newtheorem declarations.
  9. Parse §13 references → refs.bib with arXiv-ID-based bibkeys.
 10. Replace inline citations (arXiv:NNNN.NNNNN, "Author et al.,
     YEAR") with \cite{key}.

Usage:
    python -m scripts.build_paper_tex

Then in paper/:
    pdflatex paper.tex
    bibtex paper
    pdflatex paper.tex
    pdflatex paper.tex

Notes:
- This is a pragmatic best-effort converter. Output may need manual
  touch-up for unusual table shapes, deeply-nested lists, or
  exotic markdown.
- Math expressions ($..$ inline, $$..$$ display) pass through
  unchanged.
- For arXiv-style.sty, we emit an inline minimal preamble (no
  external dependency on Kourgeorge's stylesheet).
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "ARTICLE.md"
OUT_DIR = REPO / "paper"
OUT_TEX = OUT_DIR / "paper.tex"
OUT_BIB = OUT_DIR / "refs.bib"
OUT_FIGS = OUT_DIR / "figures"
OUT_README = OUT_DIR / "README.md"


# ---------------------------------------------------------------------------
# LaTeX preamble (self-contained arxiv-style preprint look)
# ---------------------------------------------------------------------------

PREAMBLE = r"""\documentclass[11pt]{article}

% --- arxiv-style preprint preamble (self-contained) --------------------------
\usepackage[a4paper,margin=1in]{geometry}
\usepackage{lmodern}      % scalable Latin Modern fonts (required by microtype expansion)
\usepackage[T1]{fontenc}
\usepackage{amsmath, amssymb, amsthm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{microtype}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage[section]{placeins}
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}
\hypersetup{
  colorlinks=true,
  linkcolor=blue,
  citecolor=blue,
  urlcolor=blue,
}
\renewcommand{\baselinestretch}{1.05}

% Map common Unicode characters that appear in the source markdown
% (math/typographic) to LaTeX-safe substitutes for pdflatex.
\usepackage{newunicodechar}
\newunicodechar{−}{$-$}    % U+2212 minus
\newunicodechar{×}{$\times$}
\newunicodechar{÷}{$\div$}
\newunicodechar{±}{$\pm$}
\newunicodechar{≈}{$\approx$}
\newunicodechar{≠}{$\neq$}
\newunicodechar{≤}{$\leq$}
\newunicodechar{≥}{$\geq$}
\newunicodechar{∈}{$\in$}
\newunicodechar{∉}{$\notin$}
\newunicodechar{∞}{$\infty$}
\newunicodechar{α}{$\alpha$}
\newunicodechar{β}{$\beta$}
\newunicodechar{γ}{$\gamma$}
\newunicodechar{δ}{$\delta$}
\newunicodechar{ε}{$\varepsilon$}
\newunicodechar{ζ}{$\zeta$}
\newunicodechar{η}{$\eta$}
\newunicodechar{θ}{$\theta$}
\newunicodechar{κ}{$\kappa$}
\newunicodechar{λ}{$\lambda$}
\newunicodechar{μ}{$\mu$}
\newunicodechar{π}{$\pi$}
\newunicodechar{ρ}{$\rho$}
\newunicodechar{σ}{$\sigma$}
\newunicodechar{τ}{$\tau$}
\newunicodechar{φ}{$\varphi$}
\newunicodechar{χ}{$\chi$}
\newunicodechar{ψ}{$\psi$}
\newunicodechar{ω}{$\omega$}
\newunicodechar{Δ}{$\Delta$}
\newunicodechar{Σ}{$\Sigma$}
\newunicodechar{Π}{$\Pi$}
\newunicodechar{Ω}{$\Omega$}
\newunicodechar{Ψ}{$\Psi$}
\newunicodechar{ℝ}{$\mathbb{R}$}
\newunicodechar{ℕ}{$\mathbb{N}$}
\newunicodechar{ℤ}{$\mathbb{Z}$}
\newunicodechar{·}{$\cdot$}
\newunicodechar{…}{\ldots}
\newunicodechar{—}{---}     % em dash
\newunicodechar{–}{--}      % en dash
\newunicodechar{‘}{`}
\newunicodechar{’}{'}
\newunicodechar{“}{``}
\newunicodechar{”}{''}
\newunicodechar{§}{\S}
\newunicodechar{ℓ}{$\ell$}
\newunicodechar{✓}{\checkmark}
\newunicodechar{✗}{$\times$}
\newunicodechar{🟢}{}
\newunicodechar{🟡}{}
\newunicodechar{⏸}{}
\newunicodechar{⇒}{$\Rightarrow$}
\newunicodechar{⇐}{$\Leftarrow$}
\newunicodechar{⇔}{$\Leftrightarrow$}
\newunicodechar{→}{$\to$}
\newunicodechar{←}{$\leftarrow$}
\newunicodechar{↔}{$\leftrightarrow$}
\newunicodechar{↑}{$\uparrow$}
\newunicodechar{↓}{$\downarrow$}
\newunicodechar{∂}{$\partial$}
\newunicodechar{∇}{$\nabla$}
\newunicodechar{∼}{$\sim$}
\newunicodechar{∝}{$\propto$}
\newunicodechar{⊂}{$\subset$}
\newunicodechar{⊃}{$\supset$}
\newunicodechar{⊆}{$\subseteq$}
\newunicodechar{⊇}{$\supseteq$}
\newunicodechar{∪}{$\cup$}
\newunicodechar{∩}{$\cap$}
\newunicodechar{∅}{$\emptyset$}
\newunicodechar{∀}{$\forall$}
\newunicodechar{∃}{$\exists$}
\newunicodechar{∧}{$\wedge$}
\newunicodechar{∨}{$\vee$}
\newunicodechar{¬}{$\neg$}
\newunicodechar{∑}{$\sum$}
\newunicodechar{∏}{$\prod$}
\newunicodechar{∫}{$\int$}
\newunicodechar{√}{$\sqrt{}$}
\newunicodechar{ℓ}{$\ell$}
\newunicodechar{†}{$\dagger$}
\newunicodechar{‡}{$\ddagger$}
\newunicodechar{°}{$^{\circ}$}
\newunicodechar{²}{$^2$}
\newunicodechar{³}{$^3$}
\newunicodechar{¹}{$^1$}
\newunicodechar{½}{$\frac{1}{2}$}
\newunicodechar{¼}{$\frac{1}{4}$}
\newunicodechar{¾}{$\frac{3}{4}$}
\newunicodechar{⌈}{$\lceil$}
\newunicodechar{⌉}{$\rceil$}
\newunicodechar{⌊}{$\lfloor$}
\newunicodechar{⌋}{$\rfloor$}
\newunicodechar{⟨}{$\langle$}
\newunicodechar{⟩}{$\rangle$}
\newunicodechar{‖}{$\|$}
\newunicodechar{∥}{$\|$}
\newunicodechar{‐}{-}
\newunicodechar{‑}{-}
\newunicodechar{ᵀ}{$^{\top}$}
\newunicodechar{·}{$\cdot$}
\newunicodechar{‹}{$<$}
\newunicodechar{›}{$>$}
\newunicodechar{«}{``}
\newunicodechar{»}{''}
\newunicodechar{ι}{$\iota$}
\newunicodechar{ν}{$\nu$}
\newunicodechar{ξ}{$\xi$}
\newunicodechar{ο}{o}
\newunicodechar{Φ}{$\Phi$}
\newunicodechar{Λ}{$\Lambda$}
\newunicodechar{Θ}{$\Theta$}
\newunicodechar{Γ}{$\Gamma$}
\newunicodechar{Ξ}{$\Xi$}
\newunicodechar{Υ}{$\Upsilon$}
\newunicodechar{Β}{B}
\newunicodechar{ⁿ}{$^{n}$}
\newunicodechar{₀}{$_0$}
\newunicodechar{₁}{$_1$}
\newunicodechar{₂}{$_2$}
\newunicodechar{₃}{$_3$}
\newunicodechar{₄}{$_4$}
\newunicodechar{₅}{$_5$}
\newunicodechar{ᵢ}{$_i$}
\newunicodechar{ⱼ}{$_j$}
\newunicodechar{ₜ}{$_t$}
\newunicodechar{₊}{$_+$}
\newunicodechar{₋}{$_-$}
\newunicodechar{∘}{$\circ$}
\newunicodechar{⊗}{$\otimes$}
\newunicodechar{⊕}{$\oplus$}
\newunicodechar{≡}{$\equiv$}


% Theorem environments for Lemma 1, Corollaries 1 & 2, Conjecture 1.
\theoremstyle{plain}
\newtheorem{lemma}{Lemma}
\newtheorem{corollary}{Corollary}
\theoremstyle{definition}
\newtheorem{conjecture}{Conjecture}

% Allow long URLs and arXiv IDs to break in references.
\hypersetup{breaklinks=true}
\sloppy

% --- title block (user must fill in author block before submission) ---------
\title{Endogenous attractor regimes in recursive large-language-model loops:\\
       What does it cost to nudge an LLM out of an attractor?\\
       A theoretical framework with measured barrier heights in tokens.}
\author{[Author Name]\\{}[Affiliation]\\\texttt{[email]}}
\date{\today}

\begin{document}
\maketitle

"""

POSTAMBLE = r"""

\bibliographystyle{plainnat}
\bibliography{refs}

\end{document}
"""


# ---------------------------------------------------------------------------
# Inline-pattern translators (markdown ↔ LaTeX)
# ---------------------------------------------------------------------------

# Order matters: process code/math first to protect them from later
# transformations.

def _escape_special_chars(text: str) -> str:
    """Escape LaTeX-special characters that don't appear inside math
    or code spans. This runs after math/code have been replaced with
    placeholders, so we don't need to worry about $-escaping math."""
    # Order matters: do backslash before others
    out = text
    # underscore in normal text → \_
    # but only when not inside a \cite{} or \href{} (those handled separately)
    # We'll do a coarse pass: escape _, %, &, #, ~ (but NOT $ or \ — math
    # has been replaced with placeholders by the time we get here).
    out = re.sub(r"(?<!\\)([%&#])", r"\\\1", out)
    # Don't try to escape ~ (used in URLs) or _ (would break too many cases)
    return out


def _convert_math_blocks(text: str) -> tuple[str, list[str]]:
    """Replace $$...$$ display-math blocks AND inline $..$ math with
    placeholders so they pass through inline-text rewriters unchanged.
    The placeholders distinguish the two so we can restore differently.
    Returns (rewritten_text, list_of_blocks_typed)."""
    blocks: list[tuple[str, str]] = []  # list of (kind, body)
    def _stash_display(m: re.Match) -> str:
        blocks.append(("display", m.group(1)))
        return f"\x00MATHBLOCK{len(blocks)-1}\x00"
    def _stash_inline(m: re.Match) -> str:
        blocks.append(("inline", m.group(1)))
        return f"\x00MATHBLOCK{len(blocks)-1}\x00"
    # Display math first (avoid re-matching $..$ inside $$..$$)
    rewritten = re.sub(r"\$\$([\s\S]*?)\$\$", _stash_display, text)
    # Inline math: $...$ — body excludes `$`, may span single
    # newlines (multi-line inline math like
    # `$\mathrm{B} \le \kappa\n\approx 80$`) but NOT paragraph
    # breaks (\n\s*\n) — otherwise a stray `$30` (currency) would
    # swallow text up to the next `$` arbitrarily far away.
    rewritten = re.sub(
        r"(?<!\$)\$((?:(?!\$|\n\s*\n)[\s\S])+?)\$(?!\$)",
        _stash_inline, rewritten,
    )
    return rewritten, blocks


def _restore_math_blocks(text: str, blocks: list[tuple[str, str]]) -> str:
    for i, (kind, b) in enumerate(blocks):
        if kind == "display":
            replacement = "\\begin{equation*}\n" + b.strip() + "\n\\end{equation*}"
        else:
            replacement = "$" + b + "$"
        text = text.replace(f"\x00MATHBLOCK{i}\x00", replacement)
    return text


def _convert_fenced_code(text: str) -> tuple[str, list[str]]:
    """Replace fenced ```lang...``` blocks with placeholders so the
    inline-backtick rewriter doesn't accidentally consume their
    content. Returns (rewritten_text, list_of_blocks)."""
    blocks: list[str] = []
    def _stash(m: re.Match) -> str:
        blocks.append(m.group(2))  # body without lang label
        return f"\x00CODEBLOCK{len(blocks)-1}\x00"
    # ```optional_lang\n...\n```
    rewritten = re.sub(
        r"```([a-zA-Z0-9_+\-]*)\n([\s\S]*?)\n```",
        _stash, text,
    )
    return rewritten, blocks


_VERBATIM_UNICODE_MAP = {
    "‖": "||",   "ε": "eps", "τ": "tau",  "λ": "lambda", "ρ": "rho",
    "σ": "sigma","θ": "theta","κ": "kappa","α": "alpha","β": "beta",
    "γ": "gamma","δ": "delta","Δ": "Delta","Σ": "Sigma","π": "pi",
    "η": "eta", "μ": "mu",   "φ": "phi",  "ψ": "psi",   "Ω": "Omega",
    "≈": "~=",  "≠": "!=",   "≤": "<=",   "≥": ">=",
    "∈": "in",  "∉": "not_in","∞": "inf",
    "⇒": "=>",  "⇐": "<=",   "⇔": "<=>", "→": "->",  "←": "<-",
    "↔": "<->", "↑": "^",    "↓": "v",
    "−": "-",   "×": "x",    "÷": "/",   "±": "+/-",
    "·": ".",   "…": "...",  "—": "--",  "–": "-",
    "²": "^2",  "³": "^3",   "₀": "_0",  "₁": "_1", "₂": "_2",
    "₃": "_3",  "₄": "_4",   "₅": "_5",
    "ℝ": "R",   "ℕ": "N",    "ℤ": "Z",
    "∂": "d",   "∇": "grad", "∼": "~",   "∝": "prop",
    "∧": "and", "∨": "or",   "¬": "not",
    "∑": "sum", "∏": "prod", "∫": "int", "√": "sqrt",
    "ℓ": "l",   "°": "deg",  "§": "S",
    "‘": "'",   "’": "'",    "“": '"',   "”": '"',
}


def _restore_fenced_code(text: str, blocks: list[str]) -> str:
    """Restore fenced ``` blocks as `\\begin{verbatim}...\\end{verbatim}`.
    Verbatim doesn't go through `\\newunicodechar` substitution, so we
    replace unicode chars with ASCII fallbacks at restoration time.
    Strategy:
      1. Apply named substitutions from _VERBATIM_UNICODE_MAP for
         common math/typographic chars.
      2. For any remaining non-ASCII char, fall back to NFKD
         compatibility decomposition + drop combining marks; if that
         still leaves non-ASCII bytes, replace with `?`."""
    import unicodedata
    def _asciify(s: str) -> str:
        for u, a in _VERBATIM_UNICODE_MAP.items():
            s = s.replace(u, a)
        out_chars: list[str] = []
        for ch in s:
            if ord(ch) < 128:
                out_chars.append(ch)
                continue
            # Try compatibility decomposition (e.g., z̄ → z + combining)
            decomp = unicodedata.normalize("NFKD", ch)
            ascii_only = "".join(c for c in decomp if ord(c) < 128)
            if ascii_only:
                out_chars.append(ascii_only)
            else:
                out_chars.append("?")
        return "".join(out_chars)
    for i, b in enumerate(blocks):
        text = text.replace(
            f"\x00CODEBLOCK{i}\x00",
            "\\begin{verbatim}\n" + _asciify(b) + "\n\\end{verbatim}",
        )
    return text


def _convert_inline_code(text: str) -> str:
    """Convert `code` to \\texttt{code} (after escaping LaTeX-special
    characters that would otherwise break inside \\texttt{} text
    mode)."""
    def _ttify(m: re.Match) -> str:
        s = m.group(1)
        # Order matters: backslash first so subsequent backslash-
        # introducing escapes (\_, \&, etc.) aren't double-escaped.
        s = s.replace("\\", r"\textbackslash{}")
        s = s.replace("{", r"\{")
        s = s.replace("}", r"\}")
        s = s.replace("_", r"\_")
        s = s.replace("&", r"\&")
        s = s.replace("#", r"\#")
        s = s.replace("%", r"\%")
        s = s.replace("$", r"\$")
        s = s.replace("^", r"\textasciicircum{}")
        s = s.replace("~", r"\textasciitilde{}")
        return r"\texttt{" + s + "}"
    return re.sub(r"`([^`]+)`", _ttify, text)


def _convert_inline_emphasis(text: str) -> str:
    """**bold** → \\textbf{...}; *italic* → \\textit{...}.

    Order matters AND nesting matters. Markdown allows
    `**bold with *italic* inside**`. We:
      1. Stash backslash-escaped asterisks (`\\*`) as placeholders.
      2. Run bold first, allowing internal `*` characters in the
         body (so nested italic markers don't break the match), but
         restricted to a single line (no spanning paragraphs).
      3. Run italic on the whole text afterward — the italic
         markers that were inside `\\textbf{...}` are still single-`*`
         tokens and will be picked up.
      4. Restore literal asterisks."""
    text = text.replace(r"\*", "\x00ESCASTERISK\x00")
    # Bold: non-greedy, allow newlines in the body but not paragraph
    # breaks (\n\s*\n). Body is "anything that doesn't contain '**'
    # or a paragraph break".
    text = re.sub(
        r"\*\*((?:(?!\*\*|\n\s*\n)[\s\S])+?)\*\*",
        r"\\textbf{\1}", text,
    )
    # Italic: single `*` not adjacent to another `*` (avoids
    # mismatching the closing marker of an already-converted bold).
    text = re.sub(r"(?<![*\\])\*([^*\n]+?)\*(?!\*)", r"\\textit{\1}", text)
    text = text.replace("\x00ESCASTERISK\x00", "*")
    return text


def _convert_links(text: str) -> str:
    """[text](url) → \href{url}{text}."""
    def _href(m: re.Match) -> str:
        link_text = m.group(1)
        url = m.group(2)
        # don't \href image-alts (those handled separately as figures)
        return r"\href{" + url + "}{" + link_text + "}"
    # Match [text](url) but not ![alt](path) (image)
    return re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", _href, text)


def _convert_inline_math(text: str) -> str:
    """Inline $..$ → leave as-is (LaTeX compatible). Just verify
    pairs match. No-op pass-through."""
    return text


# ---------------------------------------------------------------------------
# Block-level translators
# ---------------------------------------------------------------------------

def _convert_headings(text: str) -> str:
    """Convert ##/###/#### to LaTeX section commands."""
    out_lines: list[str] = []
    for line in text.split("\n"):
        if line.startswith("#### "):
            out_lines.append(r"\subsubsection{" + line[5:].strip() + "}")
        elif line.startswith("### "):
            out_lines.append(r"\subsection{" + line[4:].strip() + "}")
        elif line.startswith("## "):
            out_lines.append(r"\section{" + line[3:].strip() + "}")
        elif line.startswith("# "):
            # top-level title — already in preamble; emit as paragraph break
            continue
        else:
            out_lines.append(line)
    return "\n".join(out_lines)


def _convert_lists(text: str) -> str:
    """Convert markdown - / 1. lists to itemize / enumerate.
    Naive: only handles top-level lists, not nesting."""
    lines = text.split("\n")
    out: list[str] = []
    in_itemize = False
    in_enumerate = False
    for line in lines:
        m_ul = re.match(r"^(\s*)-\s+(.+)$", line)
        m_ol = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if m_ul:
            if in_enumerate:
                out.append(r"\end{enumerate}")
                in_enumerate = False
            if not in_itemize:
                out.append(r"\begin{itemize}")
                in_itemize = True
            out.append(r"  \item " + m_ul.group(2))
        elif m_ol:
            if in_itemize:
                out.append(r"\end{itemize}")
                in_itemize = False
            if not in_enumerate:
                out.append(r"\begin{enumerate}")
                in_enumerate = True
            out.append(r"  \item " + m_ol.group(2))
        else:
            if in_itemize:
                out.append(r"\end{itemize}")
                in_itemize = False
            if in_enumerate:
                out.append(r"\end{enumerate}")
                in_enumerate = False
            out.append(line)
    if in_itemize:
        out.append(r"\end{itemize}")
    if in_enumerate:
        out.append(r"\end{enumerate}")
    return "\n".join(out)


def _split_table_row(line: str) -> list[str]:
    """Split a markdown table row on `|`, respecting brace depth so
    that `|` characters inside `\\texttt{...}` (or any LaTeX command
    body) are not treated as column separators."""
    body = line.strip().strip("|")
    cells: list[str] = []
    cur: list[str] = []
    depth = 0
    for ch in body:
        if ch == "{":
            depth += 1
            cur.append(ch)
        elif ch == "}":
            depth = max(0, depth - 1)
            cur.append(ch)
        elif ch == "|" and depth == 0:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    cells.append("".join(cur).strip())
    return cells


def _convert_tables(text: str) -> str:
    """Convert markdown pipe tables to LaTeX tabular environments.
    Detects header line followed by separator line (---) followed by
    data rows. Cell-splitter is brace-aware so `|` inside
    `\\texttt{...}` (already converted from backticks) is preserved."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect table: "| ... |" header, "|---|...|" separator
        if (line.strip().startswith("|") and i + 1 < len(lines)
                and re.match(r"^\s*\|[\s\-:|]+\|\s*$", lines[i + 1])):
            # collect table rows
            header = _split_table_row(line)
            sep_line = lines[i + 1]
            # column alignments from separator
            alignments = []
            for col in sep_line.strip().strip("|").split("|"):
                col = col.strip()
                if col.startswith(":") and col.endswith(":"):
                    alignments.append("c")
                elif col.endswith(":"):
                    alignments.append("r")
                else:
                    alignments.append("l")
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(_split_table_row(lines[j]))
                j += 1
            # Emit tabular
            col_spec = "".join(alignments)
            out.append(r"\begin{table}[h!]")
            out.append(r"\centering")
            out.append(r"\small")
            out.append(r"\begin{tabular}{" + col_spec + "}")
            out.append(r"\toprule")
            out.append(" & ".join(c for c in header) + r" \\")
            out.append(r"\midrule")
            for row in rows:
                # pad row to header length
                while len(row) < len(header):
                    row.append("")
                out.append(" & ".join(row[:len(header)]) + r" \\")
            out.append(r"\bottomrule")
            out.append(r"\end{tabular}")
            out.append(r"\end{table}")
            i = j
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def _convert_figures(text: str, fig_target_dir: Path) -> str:
    """Walk `![Caption](path/to.png)` and replace with figure
    environment, copying the PNG to fig_target_dir.

    Captions often contain inner parens like `(joint t-SNE)`, so we
    can't use a naive `[^)]+` for the path. Instead we anchor the
    path pattern to the end of the line: it ends with `.png)`."""
    fig_target_dir.mkdir(parents=True, exist_ok=True)
    out: list[str] = []
    counter = 0
    for line in text.split("\n"):
        m = re.match(r"^\s*!\[(.+)\]\(([^)]+\.(?:png|jpg|jpeg|pdf))\)\s*$", line)
        if not m:
            out.append(line)
            continue
        counter += 1
        caption = m.group(1)
        src_path = REPO / m.group(2)
        # Caption often starts with "Figure N. " — strip that prefix
        cap_clean = re.sub(r"^Figure\s+\d+\.\s*", "", caption).strip()
        if src_path.exists():
            target_name = f"fig{counter:02d}.png"
            shutil.copyfile(src_path, fig_target_dir / target_name)
            includegraphics_path = f"figures/{target_name}"
        else:
            includegraphics_path = m.group(2)  # leave dangling for user fix
        out.append(r"\begin{figure}[h!]")
        out.append(r"\centering")
        out.append(r"\includegraphics[width=0.95\linewidth]{" + includegraphics_path + "}")
        out.append(r"\caption{" + cap_clean + "}")
        out.append(r"\end{figure}")
    return "\n".join(out)


def _escape_prose_specials(text: str) -> str:
    """Escape LaTeX-special characters in prose.

    State-aware:
      - Inside `\\begin{verbatim}...\\end{verbatim}`: leave everything alone.
      - Inside `\\begin{tabular}...\\end{tabular}`: leave `&` (column
        separator), but ESCAPE `%` and `#` (still LaTeX-special inside
        tables — `%` would comment-out the rest of the row including
        `\\\\` and `\\bottomrule`!).
      - Elsewhere: escape `&`, `%`, `#`."""
    out_lines: list[str] = []
    in_tabular = False
    in_verbatim = False
    for line in text.split("\n"):
        if r"\begin{tabular}" in line:
            in_tabular = True
        if r"\begin{verbatim}" in line:
            in_verbatim = True
        if not in_verbatim:
            # % must always be escaped (except in verbatim) — it starts
            # a LaTeX comment otherwise and silently eats the rest of
            # the line, including \\bottomrule etc.
            line = re.sub(r"(?<!\\)%", r"\\%", line)
            # # is parameter char in macros; escape outside verbatim.
            line = re.sub(r"(?<!\\)#", r"\\#", line)
            # $ (dollar) is math-mode toggle. Math has been stashed by
            # _convert_math_blocks before this pass, so any remaining $
            # is a literal currency / numeric-prefix sign that must be
            # escaped to avoid pdfTeX entering math mode.
            line = re.sub(r"(?<!\\)\$", r"\\$", line)
            # _ (underscore) is math-subscript marker outside math.
            # Common in technical prose (rolling_k3, context_tail,
            # last_user_turn, etc.) when the markdown didn't bracket
            # them in backticks. Escape to \_. Already-escaped \_ from
            # earlier \texttt{} processing is left alone via the
            # negative lookbehind.
            line = re.sub(r"(?<!\\)_", r"\\_", line)
            if not in_tabular:
                # & is column-separator in tabular envs; only escape
                # outside them.
                line = re.sub(r"(?<!\\)&", r"\\&", line)
        if r"\end{tabular}" in line:
            in_tabular = False
        if r"\end{verbatim}" in line:
            in_verbatim = False
        out_lines.append(line)
    return "\n".join(out_lines)


def _convert_theorem_envs(text: str) -> str:
    """Wrap Lemma 1, Corollary 1, Corollary 2, Conjecture 1 blocks
    in proper LaTeX theorem environments. Also wrap proofs.

    Pattern:
        \textbf{Lemma 1 (...)}.   ...body...   $\square$
    →
        \begin{lemma}[...]   body   \end{lemma}
    """
    # Lemma 1 (caption). body
    text = re.sub(
        r"\\textbf\{Lemma 1 \(([^)]+)\)\}\.\s*",
        r"\\begin{lemma}[\1]\n",
        text,
    )
    # Corollary N (caption). body
    text = re.sub(
        r"\\textbf\{Corollary (\d+) \(([^)]+)\)\}\.\s*",
        r"\\begin{corollary}[\2]\n",
        text,
    )
    # Conjecture 1 (caption).
    text = re.sub(
        r"\\textbf\{Conjecture 1 \(([^)]+)\)\}\.\s*",
        r"\\begin{conjecture}[\1]\n",
        text,
    )
    # Close at $\square$ (proof end) for Lemma 1 / Corollary
    # Note: we have to manually close the env. Naive: close at the
    # \square symbol. We use a marker pattern.
    # Pragmatic: leave a TODO comment for the user to manually close
    # since the proofs span multi-paragraph and don't have a clean
    # closing token.
    return text


# ---------------------------------------------------------------------------
# Bibliography handling
# ---------------------------------------------------------------------------

def _slugify_bibkey(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "", s).lower()
    return s[:30]


def _parse_references_section(article_text: str) -> tuple[str, dict]:
    """Find §13 References section, parse each bullet entry, and
    return (article_with_§13_replaced_with_placeholder, refs_dict).

    refs_dict maps bibkey → BibTeX entry string."""
    # Locate "## 13. References" header and capture the body until
    # next ##-level header or end of file.
    m = re.search(
        r"##\s*13\.\s*References\s*\n([\s\S]*?)(?=\n##\s|\Z)",
        article_text,
    )
    if not m:
        return article_text, {}
    refs_body = m.group(1)
    # Extract lines that look like bullet references "- arXiv:..." or
    # "- Author et al. (YEAR). *Title*. venue."
    refs: dict[str, str] = {}
    cur_lines: list[str] = []
    def _flush():
        if not cur_lines:
            return
        entry = " ".join(l.strip() for l in cur_lines).strip()
        if not entry:
            return
        bibkey, bib = _entry_to_bibtex(entry)
        if bibkey:
            refs[bibkey] = bib
    for line in refs_body.split("\n"):
        if line.strip().startswith("- "):
            _flush()
            cur_lines = [line.strip()[2:]]
        elif line.strip().startswith("**") or line.strip().startswith("##"):
            # subheading inside §13 (e.g., "**Iterative refinement...**")
            _flush()
            cur_lines = []
        elif line.strip() and cur_lines:
            cur_lines.append(line.strip())
        else:
            _flush()
            cur_lines = []
    _flush()
    return article_text, refs


def _entry_to_bibtex(entry: str) -> tuple[str | None, str | None]:
    """Best-effort parsing of one human-readable reference bullet to
    BibTeX. Returns (bibkey, bibtex) or (None, None) on failure.

    Three entry shapes are recognized:
        (A) arXiv:NNNN.NNNNN. AuthorList (YEAR). *Title*. Venue.
        (B) arXiv:NNNN.NNNNN. *Title*. (Month YEAR.) Description.
        (C) AuthorList (YEAR). *Title*. Venue.
    """
    # 1. arXiv ID detection (governs whether we strip an "arXiv:..." prefix)
    arxiv_m = re.search(r"arXiv:(\d{4}\.\d{4,5})", entry)
    arxiv_id = arxiv_m.group(1) if arxiv_m else None

    # Strip a leading "arXiv:NNNN.NNNNN." prefix if present so the
    # rest of the parser sees a clean entry.
    body = entry
    if arxiv_id:
        body = re.sub(r"^arXiv:" + re.escape(arxiv_id) + r"\.\s*", "", body)

    # 2. Year: look for (YYYY) where YYYY is 19xx-21xx, or (Month YYYY).
    year_m = (
        re.search(r"\((?:[A-Za-z]+\s+)?((?:19|20|21)\d{2})\)", body)
        or re.search(r"\b((?:19|20|21)\d{2})\b", body)
    )
    if year_m:
        year = year_m.group(1)
    elif arxiv_id:
        # arXiv year prefix: "2510" → 2025
        prefix = arxiv_id[:2]
        year = "20" + prefix if prefix.startswith("0") or int(prefix) <= 30 else "19" + prefix
    else:
        year = "0000"

    # 3. Title: the *...* italicized chunk
    title_m = re.search(r"\*([^*]+)\*", body)
    title = title_m.group(1).strip().rstrip(".") if title_m else ""
    if not title:
        # If no italic title, take the segment between "(YEAR)." and "."
        if year_m:
            after_year = body[year_m.end():].lstrip(". ")
            title = after_year.split(".")[0].strip()
        if not title:
            title = "Untitled"

    # 4. Authors: text BEFORE the year-paren, OR before the title-italic.
    if year_m:
        authors_chunk = body[:year_m.start()].rstrip().rstrip(",").rstrip(".")
    elif title_m:
        authors_chunk = body[:title_m.start()].rstrip().rstrip(",").rstrip(".")
    else:
        authors_chunk = ""

    # Drop a leading "Shape (B)" pattern where the title comes before
    # any author info (arXiv-only entries with no listed author).
    if authors_chunk.strip().startswith("*"):
        authors_chunk = ""

    authors_chunk = authors_chunk.strip()
    if not authors_chunk:
        authors_chunk = "Anonymous"

    # BibTeX wants " and " between authors, not commas. Our markdown
    # entries use comma-separated "Last, F., Last, F., ..." which
    # bibtex would otherwise misread as one author with too many
    # commas. Normalize: a "., " or "et al, " pattern marks an
    # author boundary.
    authors_chunk = authors_chunk.replace(" & ", " and ")
    # Replace ". X.," patterns (initial period + comma) with " and ".
    authors_chunk = re.sub(r"\.\s*,\s*(?=[A-ZŞŁÅÇÉÈÄÖÜ])", ". and ", authors_chunk)
    # "et al" → "et al." properly terminated
    authors_chunk = re.sub(r"\bet al\b\.?", "et al.", authors_chunk)

    # 5. First-author-last-name for bibkey
    first_author_part = authors_chunk.split(",")[0].split(" et al")[0].strip()
    first_author_last = first_author_part.split()[-1] if first_author_part else "anon"

    # 6. Bibkey
    if arxiv_id:
        bibkey = f"arxiv{arxiv_id.replace('.', '')}"
    else:
        bibkey = _slugify_bibkey(first_author_last + year)
        if bibkey.startswith("0000") or len(bibkey) < 5:
            bibkey = _slugify_bibkey(first_author_last + year + title[:8])

    # 7. Venue (between *Title*. and end)
    venue = ""
    if title_m:
        after_title = body[title_m.end():].lstrip(". ")
        venue_m = re.match(r"^([^.]+)", after_title)
        if venue_m:
            venue = venue_m.group(1).strip()

    # 8. Build BibTeX
    if arxiv_id:
        bib = (f"@misc{{{bibkey},\n"
               f"  title = {{{title}}},\n"
               f"  author = {{{authors_chunk}}},\n"
               f"  year = {{{year}}},\n"
               f"  eprint = {{{arxiv_id}}},\n"
               f"  archivePrefix = {{arXiv}}\n"
               f"}}\n")
    else:
        bib = (f"@article{{{bibkey},\n"
               f"  title = {{{title}}},\n"
               f"  author = {{{authors_chunk}}},\n"
               f"  year = {{{year}}},\n"
               f"  journal = {{{venue}}}\n"
               f"}}\n")
    return bibkey, bib


def _replace_inline_citations(text: str, refs: dict) -> str:
    """Replace inline citation patterns with \cite{key}.
    Handles `arXiv:NNNN.NNNNN` → \cite{arxivNNNNNNNNN}."""
    def _arxiv(m: re.Match) -> str:
        arxiv_id = m.group(1)
        bibkey = f"arxiv{arxiv_id.replace('.', '')}"
        if bibkey in refs:
            return f"\\cite{{{bibkey}}}"
        return m.group(0)
    text = re.sub(r"arXiv:(\d{4}\.\d{4,5})", _arxiv, text)
    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FIGS.mkdir(parents=True, exist_ok=True)

    article_text = SRC.read_text(encoding="utf-8")

    # Strip ## Abstract + everything in it from main flow — emit as
    # \begin{abstract} ... \end{abstract} after \maketitle.
    abstract_m = re.search(r"##\s*Abstract\s*\n([\s\S]*?)(?=\n##\s)", article_text)
    abstract_body = abstract_m.group(1).strip() if abstract_m else ""
    if abstract_m:
        article_text = article_text[:abstract_m.start()] + article_text[abstract_m.end():]

    # Parse and remove §13 References (we emit BibTeX file separately)
    article_text, refs = _parse_references_section(article_text)
    # Remove the §13 section from article_text body
    article_text = re.sub(
        r"##\s*13\.\s*References[\s\S]*?(?=\n##\s|\Z)",
        "",
        article_text,
    )

    # Remove the top-level "# Title\n" line and any subtitle "## Subtitle"
    article_text = re.sub(r"^#\s+.+?\n", "", article_text)
    article_text = re.sub(r"^##\s+What does it cost.+?\n", "", article_text, count=1)

    # Stash math blocks ($$..$$) and fenced code blocks (```...```)
    # so they pass through every other rewrite unchanged.
    article_text, math_blocks = _convert_math_blocks(article_text)
    article_text, code_blocks = _convert_fenced_code(article_text)

    # Figures FIRST — captions can contain markdown emphasis and
    # inline-code spans whose underscores would otherwise get escaped
    # before the path could be picked up.
    article_text = _convert_figures(article_text, OUT_FIGS)

    # Inline patterns
    article_text = _convert_inline_code(article_text)
    article_text = _convert_inline_emphasis(article_text)
    article_text = _convert_links(article_text)
    article_text = _replace_inline_citations(article_text, refs)

    # Block patterns
    article_text = _convert_tables(article_text)
    article_text = _convert_lists(article_text)
    article_text = _convert_headings(article_text)
    article_text = _convert_theorem_envs(article_text)

    # Escape LaTeX-special prose characters (&, #, %). State-aware:
    # & only outside tables; # and % everywhere except verbatim.
    article_text = _escape_prose_specials(article_text)

    # Restore code + math blocks now that text rewrites are done
    article_text = _restore_fenced_code(article_text, code_blocks)
    article_text = _restore_math_blocks(article_text, math_blocks)

    # Strip horizontal rule lines
    article_text = re.sub(r"^---\s*$", "", article_text, flags=re.MULTILINE)

    # Build final .tex
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

    OUT_README.write_text(_BUILD_README, encoding="utf-8")
    print(f"wrote {OUT_README}")

    n_figs = len(list(OUT_FIGS.glob("*.png")))
    print(f"copied {n_figs} figure PNGs to {OUT_FIGS}/")

    print()
    print("Build:")
    print(f"  cd {OUT_DIR.relative_to(REPO)}")
    print("  pdflatex paper.tex && bibtex paper && pdflatex paper.tex && pdflatex paper.tex")
    return 0


_BUILD_README = """# paper/

LaTeX project for the paper, generated from `../ARTICLE.md` by
`python -m scripts.build_paper_tex`.

## Build

```bash
pdflatex paper.tex
bibtex paper
pdflatex paper.tex
pdflatex paper.tex
```

## Files

- `paper.tex` — main LaTeX source (markdown-converted)
- `refs.bib` — BibTeX bibliography (extracted from ARTICLE.md §13)
- `figures/fig*.png` — copied figure PNGs (originals in `../data/`)
- `README.md` — this file

## Manual touch-ups likely needed

The converter is best-effort. Common issues:

1. **Theorem environments**: Lemma 1, Corollaries 1 & 2, and
   Conjecture 1 are opened with `\\begin{lemma}`, `\\begin{corollary}`,
   `\\begin{conjecture}`. Closing tags (`\\end{lemma}` etc.) need to
   be inserted manually because the proofs span multi-paragraph and
   no clean closing token can be auto-detected.
2. **Author block**: `[Author Name]`, `[Affiliation]`, `[email]`
   placeholders in `paper.tex` need to be filled in.
3. **arXiv submission**: arXiv accepts the resulting PDF directly.
   Compile with the build commands above and upload `paper.pdf`.
4. **Reference format**: bibkeys for arXiv-prefixed entries follow
   `arxivNNNNNNNNN` style (e.g., `arxiv251210350`); for others,
   `firstauthorYYYY` style. Check `refs.bib` for any entries missing
   author / year if your bibliography style requires them.
5. **Tables**: complex pipe-tables with multi-line cells may need
   manual cleanup. Most simple tables transfer cleanly.
6. **Cross-references**: `(see §5.5)` markdown text becomes literal
   text in LaTeX. To get clickable references, replace with
   `\\autoref{sec:5.5}` and add `\\label{sec:5.5}` to the
   `\\subsection{}` line.

Re-run `python -m scripts.build_paper_tex` after editing ARTICLE.md
to regenerate.
"""


if __name__ == "__main__":
    raise SystemExit(main())
