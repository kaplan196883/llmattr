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

PREAMBLE = r"""\documentclass{article}

% --- Kourgeorge arxiv.sty preprint look --------------------------------------
% Provides: Times+Helvetica fonts, letter geometry (6.5x9in), fancy header
% with "A Preprint" + title + page number, horizontal-rule title box,
% small-caps centered Abstract environment, tighter section spacing.
\usepackage{arxiv}

% Encoding (explicit per Kourgeorge template)
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}

% Math
\usepackage{amsmath, amssymb, amsthm}

% Tables / figures
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{caption}
\usepackage[section]{placeins}
\usepackage{footnote}    % savenotes env: lets \footnote work inside captions
\makesavenoteenv{figure}
\captionsetup{font=small,labelfont=bf}

% Microtype protrusion / expansion (works with Times via T1)
\usepackage{microtype}

% Lists
\usepackage{enumitem}

% Citations + hyperlinks (natbib MUST load before hyperref)
\usepackage{natbib}
\usepackage{hyperref}

% ORCID logo + hyperlinked iD next to author name. Falls back gracefully
% if the package is missing — pdflatex will warn but not error.
\usepackage{orcidlink}

% Allow LaTeX more flexibility in line-breaking: long file paths
% inside \texttt{...} (e.g. data/aggregated/.../scatter.png) are
% otherwise unbreakable and trigger Overfull \hbox warnings + visible
% margin overflow. \emergencystretch gives the typesetter up to 3em
% of extra glue per line as a last resort.
\setlength{\emergencystretch}{3em}
\tolerance=1000

% Wide-table support: tabularx provides the X column type which
% wraps long prose-content cells to fit within \textwidth instead of
% pushing the table off the right margin. Define a ragged-right
% variant Y — without it, default X is justified and cells with
% unbreakable runs (\texttt{...}, URLs, long camelCase) can still
% trigger "Overfull hbox in alignment" warnings.
\usepackage{tabularx}
\usepackage{array}    % \arraybackslash
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}

\usepackage{etoolbox}    % for \ifstrempty

% Pipeline / flow-diagram boxes (tcolorbox + TikZ).
% Used for §4.11 end-to-end pipeline and similar phase-structured
% diagrams. Phase boxes are titled, breakable across pages, and
% connected by short downward TikZ arrows via \flowarrow.
\usepackage[most]{tcolorbox}
\usepackage{tikz}
\usetikzlibrary{positioning, arrows.meta, fit, calc, matrix}

% Code / ASCII-art verbatim wrappers — defined AFTER tcolorbox is
% loaded. codeblock and asciiblock both render at \footnotesize with
% a thin left rule and a subtle gray background. The visual styling
% uses tcolorbox in `breakable` mode so blocks can split across pages.
% Both support an optional [caption] argument rendered as italic
% small-caps above the block.
\definecolor{codebg}{gray}{0.965}
\definecolor{coderule}{gray}{0.55}
\tcbset{codeblockstyle/.style={
  enhanced,
  breakable,
  colback=codebg,
  colframe=coderule,
  boxrule=0pt,
  leftrule=2pt,
  arc=0pt,
  outer arc=0pt,
  left=8pt,
  right=4pt,
  top=4pt,
  bottom=4pt,
  before skip=4pt,
  after skip=4pt,
  fontupper=\footnotesize
}}
\newenvironment{codeblock}[1][]{%
  \par\addvspace{2pt}%
  \ifstrempty{#1}{}{\noindent\textit{\small #1}\par\nobreak\addvspace{2pt}}%
  \begin{tcolorbox}[codeblockstyle]%
}{%
  \end{tcolorbox}\par%
}
\newenvironment{asciiblock}[1][]{%
  \par\addvspace{2pt}%
  \ifstrempty{#1}{}{\noindent\textit{\small #1}\par\nobreak\addvspace{2pt}}%
  \begin{tcolorbox}[codeblockstyle]%
}{%
  \end{tcolorbox}\par%
}

\tcbset{
  pipelinephase/.style={
    enhanced, breakable, colback=gray!4, colframe=black!55,
    fonttitle=\bfseries\sffamily\small, fontupper=\small,
    boxrule=0.5pt, arc=2pt,
    left=6pt, right=6pt, top=4pt, bottom=4pt,
    before skip=2pt, after skip=2pt,
    title={#1}
  },
  pipelinesub/.style={
    enhanced, colback=white, colframe=black!35,
    fonttitle=\bfseries\sffamily\footnotesize, fontupper=\footnotesize,
    boxrule=0.4pt, arc=1.5pt,
    left=4pt, right=4pt, top=3pt, bottom=3pt,
    before skip=2pt, after skip=2pt,
    title={#1}
  }
}
\newcommand{\flowarrow}{%
  \par\addvspace{1pt}%
  {\centering\tikz\draw[-{Stealth[length=2.8mm]}, line width=0.6pt]
       (0,0) -- (0,-0.42);\par}%
  \addvspace{1pt}%
}

\hypersetup{
  colorlinks=true,
  linkcolor=blue,
  citecolor=blue,
  urlcolor=blue,
  breaklinks=true,
}

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

% --- title block (user must fill in author block before submission) ---------
\title{Perturbation Dose Responses in Recursive LLM Loops\\[2pt]
       \large\itshape Raw switching, stochastic floors, and persistent escape\\
       \large\itshape under append, replace, and dialog updates}

% Short title for the running header on pages 2+. Without this, the
% full multi-line title gets crammed into the header.
\renewcommand{\shorttitle}{Perturbation dose responses in recursive LLM loops}

% `\\{}` (with the empty group) prevents \\ from parsing the next
% line-content as its optional vertical-space argument.
\author{Pawel Kaplanski~\orcidlink{0000-0003-2223-0870}\\{}Kaplanski Ai Lab\\\texttt{pawel@kaplanski.ai}}
\date{April 30, 2026}

% PDF metadata (per Kourgeorge template best-practice). Helps reference
% managers / pdf viewers display the paper correctly.
\hypersetup{
  pdftitle={Perturbation Dose Responses in Recursive LLM Loops},
  pdfsubject={cs.AI, cs.LG, cs.CL},
  pdfauthor={Pawel Kaplanski},
  pdfkeywords={recursive LLM loops, perturbation dose response,
    attractor-like regimes, context-update rules, basin switching,
    dialog dynamics},
}

\begin{document}
\maketitle

% Optional keywords line (rendered just under the abstract).
\keywords{recursive LLM loops \and perturbation dose response
  \and attractor-like regimes \and context-update rules
  \and basin switching \and dialog dynamics}

"""

POSTAMBLE = r"""

% Strict citation hygiene: bibliography contains only works with
% explicit \cite calls in the body. Use `\nocite{*}` here to also
% surface uncited refs.bib entries (e.g. survey-style "Further reading"
% mode).

\bibliographystyle{unsrtnat}
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


def _convert_fenced_code(text: str) -> tuple[str, list[tuple[str, str, str]]]:
    """Replace fenced ```lang [caption]\\n...\\n``` blocks with
    placeholders so the inline-backtick rewriter doesn't accidentally
    consume their content.

    Info-string convention: anything after the language tag on the
    opening fence is treated as an optional caption, e.g.
        ```python  Compute the V landscape
        ...
        ```
    The caption is then rendered as italic small text above the block.

    Returns (rewritten_text, list of (lang, caption, body) tuples)."""
    blocks: list[tuple[str, str, str]] = []
    def _stash(m: re.Match) -> str:
        lang = m.group(1).strip()
        caption = m.group(2).strip()
        body = m.group(3)
        blocks.append((lang, caption, body))
        return f"\x00CODEBLOCK{len(blocks)-1}\x00"
    # ```lang [caption text]\n body \n```
    rewritten = re.sub(
        r"```([a-zA-Z0-9_+\-]*)([^\n]*)\n([\s\S]*?)\n```",
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
    # Box-drawing (U+2500..U+257F) — preserve diagram structure with ASCII.
    "─": "-",   "━": "-",    "│": "|",   "┃": "|",
    "┌": "+",   "┐": "+",    "└": "+",   "┘": "+",
    "├": "+",   "┤": "+",    "┬": "+",   "┴": "+",   "┼": "+",
    "┏": "+",   "┓": "+",    "┗": "+",   "┛": "+",
    "┣": "+",   "┫": "+",    "┳": "+",   "┻": "+",   "╋": "+",
    "═": "=",   "║": "|",
    "╔": "+",   "╗": "+",    "╚": "+",   "╝": "+",
    "╠": "+",   "╣": "+",    "╦": "+",   "╩": "+",   "╬": "+",
    "╭": "+",   "╮": "+",    "╯": "+",   "╰": "+",
    # Block / triangle arrowheads in diagrams.
    "▶": ">",   "◀": "<",    "▲": "^",   "▼": "v",
    "►": ">",   "◄": "<",    "△": "^",   "▽": "v",
    "■": "#",   "□": "[]",   "●": "*",   "○": "o",
}


def _restore_fenced_code(
    text: str,
    blocks: list[tuple[str, str, str]],
) -> str:
    """Restore fenced ``` blocks as styled verbatim environments.

    Routing by language tag:
      - empty (no lang) → `asciiblock` (\\scriptsize) — typical for
        +-+|+ ASCII art / pipeline diagrams whose width needs the
        smaller font to fit \\textwidth.
      - any language tag (python/bash/yaml/...) → `codeblock`
        (\\footnotesize) — narrower line widths in real code, so a
        less aggressive size shift suffices.

    Verbatim doesn't go through \\newunicodechar substitution, so we
    asciify unicode chars at restoration time:
      1. Named substitutions from _VERBATIM_UNICODE_MAP.
      2. NFKD compatibility decomposition + drop non-ASCII bytes.
      3. Anything still non-ASCII becomes `?`."""
    import unicodedata
    def _asciify(s: str) -> str:
        for u, a in _VERBATIM_UNICODE_MAP.items():
            s = s.replace(u, a)
        out_chars: list[str] = []
        for ch in s:
            if ord(ch) < 128:
                out_chars.append(ch)
                continue
            decomp = unicodedata.normalize("NFKD", ch)
            ascii_only = "".join(c for c in decomp if ord(c) < 128)
            out_chars.append(ascii_only if ascii_only else "?")
        return "".join(out_chars)
    for i, (lang, caption, body) in enumerate(blocks):
        # Special passthrough: ```tex-raw  blocks emit their body
        # verbatim into the LaTeX output (NOT wrapped in verbatim).
        # Used for inline TikZ / tcolorbox diagrams whose markdown
        # source is the literal LaTeX. No unicode-asciification —
        # the body must already be LaTeX-safe.
        if lang in ("tex-raw", "latex-raw"):
            text = text.replace(f"\x00CODEBLOCK{i}\x00", body)
            continue
        env = "asciiblock" if not lang else "codeblock"
        opt = f"[{caption}]" if caption else ""
        text = text.replace(
            f"\x00CODEBLOCK{i}\x00",
            f"\\begin{{{env}}}{opt}\n"
            + "\\begin{verbatim}\n" + _asciify(body) + "\n\\end{verbatim}\n"
            + f"\\end{{{env}}}",
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
        # Hide `*` inside \texttt{} from the emphasis regex that runs
        # next; restored to a literal `*` by _convert_inline_emphasis.
        # Without this, `*` inside two adjacent inline-code spans pairs
        # up across the prose between them and produces a spurious
        # \textit{} that mangles the texttt content.
        s = s.replace("*", "\x00ESCASTERISK\x00")
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
    # Body allows single newlines (multi-line titles like
    # "*Dynamics of Agentic Loops...\nA Geometric Theory*") but bails
    # on paragraph breaks.
    text = re.sub(
        r"(?<![*\\])\*((?:[^*\n]|\n(?!\s*\n))+?)\*(?!\*)",
        r"\\textit{\1}", text,
    )
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
    """Convert ##/###/#### to LaTeX section commands.

    Strips leading numeric prefix from the heading text (`1. `, `1.1 `,
    `4.3.5 `, etc.) — LaTeX adds its own `\\section{}` numbering, so a
    literal "1.1" baked into the title produces "1.1  1.1 Phenomenon"
    in the rendered PDF.

    Headings WITHOUT a numeric prefix (e.g. `## Plain-language
    summary`, `### Why it matters`) are emitted as starred / unnumbered
    section commands (`\\section*{}`, `\\subsection*{}`). This lets us
    keep TOC-friendly numbered sections (1, 2, 3, ...) for the body
    while front-matter and per-paragraph sub-headings inside the
    plain-language summary stay out of the numbering hierarchy."""
    num_prefix = re.compile(r"^\d+(?:\.\d+)*\.?\s+")
    def _split(title: str) -> tuple[str, bool]:
        """Return (clean title, was_numbered). The bool tells the caller
        whether to use the starred / unnumbered form."""
        stripped = title.strip()
        if num_prefix.match(stripped):
            return num_prefix.sub("", stripped), True
        return stripped, False
    out_lines: list[str] = []
    for line in text.split("\n"):
        if line.startswith("#### "):
            t, numbered = _split(line[5:])
            out_lines.append(
                r"\subsubsection{" + t + "}" if numbered
                else r"\subsubsection*{" + t + "}"
            )
        elif line.startswith("### "):
            t, numbered = _split(line[4:])
            out_lines.append(
                r"\subsection{" + t + "}" if numbered
                else r"\subsection*{" + t + "}"
            )
        elif line.startswith("## "):
            t, numbered = _split(line[3:])
            out_lines.append(
                r"\section{" + t + "}" if numbered
                else r"\section*{" + t + "}"
            )
        elif line.startswith("# "):
            # top-level title — already in preamble; emit as paragraph break
            continue
        else:
            out_lines.append(line)
    return "\n".join(out_lines)


def _convert_footnotes(text: str) -> str:
    """Convert markdown footnotes [^id] / [^id]: def to LaTeX \\protect\\footnote.

    Strategy:
      1. Find all [^id]: <multi-line definition> blocks. Definitions run from
         the colon up to the next blank line, the next [^id]:, or EOF.
      2. Build a dict mapping id -> escaped definition text.
      3. Strip the definition blocks from the text.
      4. Replace each inline [^id] reference with \\protect\\footnote{<def>}.

    \\protect is required because the footnote may sit inside a moving
    argument such as \\caption{}.
    """
    # Capture definitions: [^id]: <def text>  (def can span lines until blank)
    def_pat = re.compile(
        r"^\[\^([A-Za-z0-9_]+)\]:\s*(.+?)(?=\n\s*\n|\n\[\^[A-Za-z0-9_]+\]:|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    definitions: dict[str, str] = {}
    for m in def_pat.finditer(text):
        fid = m.group(1)
        body = m.group(2).strip()
        # Collapse internal newlines in the definition to single spaces
        body = re.sub(r"\s+", " ", body)
        definitions[fid] = body

    # Strip the definition blocks from the text
    text = def_pat.sub("", text)

    # Replace inline references [^id] with \\protect\\footnote{def}
    def repl(m: re.Match) -> str:
        fid = m.group(1)
        if fid not in definitions:
            # Leave unresolved markers visible so the issue is obvious
            return f"[FOOTNOTE-MISSING-{fid}]"
        body = definitions[fid]
        # Escape LaTeX-special characters in the body. Order matters:
        # backslash first, then the others.
        body = body.replace("\\", r"\textbackslash{}")
        body = body.replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
        body = body.replace("_", r"\_").replace("$", r"\$")
        body = body.replace("{", r"\{").replace("}", r"\}")
        return r"\protect\footnote{" + body + "}"

    text = re.sub(r"\[\^([A-Za-z0-9_]+)\]", repl, text)

    # Clean up multiple consecutive blank lines left by stripped definitions
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _convert_lists(text: str) -> str:
    """Convert markdown - / 1. lists to itemize / enumerate.
    Naive: only handles top-level lists, not nesting.

    Indented continuation lines (the wrap of a bullet whose source
    spans multiple lines) are appended to the most recent \\item
    rather than ending the list — without this, multi-line italic /
    bold spans inside a bullet get split by a stray \\end{itemize}.

    Blank lines inside a list (between two consecutive items, or
    between an item and one of its continuation lines) do NOT end
    the list — otherwise each numbered item would get its own fresh
    \\begin{enumerate}, resetting the counter to 1 and rendering as
    "1. 1. 1." instead of "1. 2. 3.". A blank line only ends the
    list when the next non-blank line is neither another list item
    nor an indented continuation."""
    lines = text.split("\n")
    out: list[str] = []
    in_itemize = False
    in_enumerate = False
    pending_blanks: list[str] = []  # blank lines whose fate depends on lookahead

    def _is_list_item_or_cont(idx: int) -> bool:
        """Peek at line `idx` (and skip further blank lines) to decide
        whether the current pending blank gap is interior to a list."""
        j = idx
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j >= len(lines):
            return False
        nxt = lines[j]
        if re.match(r"^(\s*)-\s+(.+)$", nxt):
            return True
        if re.match(r"^(\s*)\d+\.\s+(.+)$", nxt):
            return True
        # An indented continuation line (starts with whitespace then
        # non-whitespace) is also part of the list.
        if re.match(r"^\s+\S", nxt):
            return True
        return False

    for i, line in enumerate(lines):
        m_ul = re.match(r"^(\s*)-\s+(.+)$", line)
        m_ol = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        is_blank = line.strip() == ""
        is_indented_cont = (
            (in_itemize or in_enumerate)
            and not m_ul and not m_ol and not is_blank
            and re.match(r"^\s+\S", line) is not None
        )
        if m_ul:
            if in_enumerate:
                out.append(r"\end{enumerate}")
                in_enumerate = False
            if not in_itemize:
                # Emit any buffered blank lines BEFORE opening the list
                # (they belong to the surrounding paragraph context).
                out.extend(pending_blanks)
                pending_blanks = []
                out.append(r"\begin{itemize}")
                in_itemize = True
            else:
                # Continuing an open list across a blank gap — keep
                # the blank lines inside the environment so paragraph
                # spacing inside items is preserved.
                out.extend(pending_blanks)
                pending_blanks = []
            out.append(r"  \item " + m_ul.group(2))
        elif m_ol:
            if in_itemize:
                out.append(r"\end{itemize}")
                in_itemize = False
            if not in_enumerate:
                out.extend(pending_blanks)
                pending_blanks = []
                out.append(r"\begin{enumerate}")
                in_enumerate = True
            else:
                out.extend(pending_blanks)
                pending_blanks = []
            out.append(r"  \item " + m_ol.group(2))
        elif is_indented_cont:
            # Continuation of the previous bullet — keep it inside the
            # list, preserving the indent so the rendered prose flows.
            # Flush any buffered blank lines into the list first.
            out.extend(pending_blanks)
            pending_blanks = []
            out.append(line)
        elif is_blank and (in_itemize or in_enumerate):
            # Hold this blank: defer the decision to close the list
            # until we see the next non-blank line.
            if _is_list_item_or_cont(i + 1):
                # Interior gap — keep blank inside the list.
                pending_blanks.append(line)
            else:
                # The list ends here. Close it, then emit the blank.
                if in_itemize:
                    out.append(r"\end{itemize}")
                    in_itemize = False
                if in_enumerate:
                    out.append(r"\end{enumerate}")
                    in_enumerate = False
                out.extend(pending_blanks)
                pending_blanks = []
                out.append(line)
        else:
            if in_itemize:
                out.append(r"\end{itemize}")
                in_itemize = False
            if in_enumerate:
                out.append(r"\end{enumerate}")
                in_enumerate = False
            out.extend(pending_blanks)
            pending_blanks = []
            out.append(line)
    if in_itemize:
        out.append(r"\end{itemize}")
    if in_enumerate:
        out.append(r"\end{enumerate}")
    out.extend(pending_blanks)
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
            # Heuristic for when to switch from plain tabular to
            # tabularx (wrapping cells):
            #  (a) 3+ columns with any cell longer than ~40 chars, OR
            #  (b) 5+ columns regardless — multi-column tables with
            #      short cells still overflow because tabular adds
            #      fixed padding (\tabcolsep) per column boundary.
            max_cell_len = max(
                (len(c) for r in [header, *rows] for c in r),
                default=0,
            )
            n_cols = len(header)
            use_tabularx = (n_cols >= 3 and max_cell_len > 40) or n_cols >= 5
            # Pull a preceding italic "Table — ..." line into the float
            # as an unnumbered \caption*{...} so it stays attached to
            # the table even when the [h!] float migrates. Looks back
            # across blank lines.
            caption_text = None
            scan = len(out) - 1
            while scan >= 0 and out[scan].strip() == "":
                scan -= 1
            if scan >= 0:
                m_cap = re.match(r"^\\textit\{Table\s*[—–-]\s*(.+)\}$", out[scan])
                if m_cap:
                    caption_text = m_cap.group(1).rstrip(".") + "."
                    # Drop the italic line and any trailing blanks
                    out = out[:scan]
                    while out and out[-1].strip() == "":
                        out.pop()
            out.append(r"\begin{table}[h!]")
            out.append(r"\centering")
            out.append(r"\small")
            if caption_text:
                out.append(r"\caption*{" + caption_text + "}")
            if use_tabularx:
                # Keep first column at its natural width, wrap the
                # remaining columns ragged-right (Y). Y = raggedright
                # X — defined in preamble; avoids "alignment overflow"
                # from justified X failing on unbreakable runs.
                xspec = alignments[0] + "".join("Y" for _ in alignments[1:])
                out.append(r"\begin{tabularx}{\textwidth}{" + xspec + "}")
            else:
                col_spec = "".join(alignments)
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
            out.append(r"\end{tabularx}" if use_tabularx else r"\end{tabular}")
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
        # Wrap each figure in savenotes so \footnote inside \caption emits
        # the footnote body at the bottom of the page (rather than just the
        # superscript marker, which is the default LaTeX behavior for
        # footnotes inside floats).
        out.append(r"\begin{savenotes}")
        out.append(r"\begin{figure}[h!]")
        out.append(r"\centering")
        out.append(r"\includegraphics[width=0.95\linewidth]{" + includegraphics_path + "}")
        out.append(r"\caption{" + cap_clean + "}")
        out.append(r"\end{figure}")
        out.append(r"\end{savenotes}")
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
        # Track BOTH \begin{tabular} and \begin{tabularx} — wide tables
        # use the latter, and without this check & gets escaped to \&
        # inside tabularx rows, breaking column separation.
        if r"\begin{tabular}" in line or r"\begin{tabularx}" in line:
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
        if r"\end{tabular}" in line or r"\end{tabularx}" in line:
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
        r"##\s*\d+\.\s*References\s*\n([\s\S]*?)(?=\n##\s|\Z)",
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
        # Unattributed entries: prefer the arXiv ID over "Anonymous" so
        # natbib renders [arXiv:2510.21258(2025)] instead of an
        # awkward [Anonymous(2025a)] / [Anonymous(2025b)] disambiguator.
        # Double braces tell BibTeX to treat the value as a single
        # non-decomposed corporate name.
        authors_chunk = (
            "{{arXiv:" + arxiv_id + "}}" if arxiv_id else "{{Anonymous}}"
        )

    # BibTeX wants " and " between authors, not commas. Our markdown
    # entries use comma-separated "Last, F., Last, F., ..." which
    # bibtex would otherwise misread as one author with too many
    # commas. Normalize: a "., " or "et al, " pattern marks an
    # author boundary.
    authors_chunk = authors_chunk.replace(" & ", " and ")
    # Replace ". X.," patterns (initial period + comma) with " and ".
    # The lookahead allows lowercase nobiliary particles ("de Lucena",
    # "van der Berg", "von Neumann") in addition to plain capitalized
    # surnames — without this, "Berg, C., de Lucena, D." stays comma-
    # separated and BibTeX merges the first two authors into one.
    authors_chunk = re.sub(r"\.\s*,\s*(?=[A-Za-zŞŁÅÇÉÈÄÖÜ])", ". and ", authors_chunk)
    # Strip a redundant " and and " that the regex above can produce
    # when the input already had ", and " (Oxford comma).
    authors_chunk = re.sub(r"\s+and\s+and\s+", " and ", authors_chunk)
    # "et al" / "et al." → BibTeX's "and others" sentinel so plainnat
    # can render proper et-al suppression. Without this, "Berg et al."
    # becomes a single malformed author and natbib emits "[et al.(YYYY)]"
    # with no surname at all.
    authors_chunk = re.sub(r"\s*,?\s*et\s+al\.?", " and others", authors_chunk)
    # Re-run the and-and cleanup: the previous separator-normalization
    # step turned ", et al." into " and et al." in some entries; the
    # et-al replacement then produces " and and others". Squash.
    authors_chunk = re.sub(r"\s+and\s+and\s+", " and ", authors_chunk)

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

    # 7. Venue + URL (between *Title*. and end). Extract any explicit
    # http(s) URL first, since URLs contain dots that would otherwise
    # truncate the venue regex below at e.g. ".com" or ".org".
    venue = ""
    url = ""
    if title_m:
        after_title = body[title_m.end():].lstrip(". ")
        url_m = re.search(r"https?://[^\s<>]+", after_title)
        if url_m:
            url = url_m.group(0).rstrip(">.,;)")
            before_url = after_title[:url_m.start()].rstrip().rstrip("<,.; ")
            venue_m = re.match(r"^([^.]+)", before_url)
            if venue_m:
                venue = venue_m.group(1).strip().rstrip(",")
        else:
            venue_m = re.match(r"^([^.]+)", after_title)
            if venue_m:
                venue = venue_m.group(1).strip()

    # 8. Build BibTeX
    if arxiv_id:
        # Include both `eprint` (semantic) and `url` (renderable by
        # unsrtnat.bst as a clickable link via hyperref). Without `url`,
        # the rendered bibliography entry contains no link to the paper.
        bib = (f"@misc{{{bibkey},\n"
               f"  title = {{{title}}},\n"
               f"  author = {{{authors_chunk}}},\n"
               f"  year = {{{year}}},\n"
               f"  eprint = {{{arxiv_id}}},\n"
               f"  archivePrefix = {{arXiv}},\n"
               f"  url = {{https://arxiv.org/abs/{arxiv_id}}}\n"
               f"}}\n")
    elif url:
        # Non-arxiv reference with an explicit URL (e.g. code archive).
        # Use @misc + howpublished so unsrtnat renders the URL as a
        # clickable link rather than truncating mid-domain.
        bib = (f"@misc{{{bibkey},\n"
               f"  title = {{{title}}},\n"
               f"  author = {{{authors_chunk}}},\n"
               f"  year = {{{year}}},\n"
               f"  howpublished = {{\\url{{{url}}}}},\n"
               f"  note = {{{venue}}}\n"
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
    """Replace inline `arXiv:NNNN.NNNNN` patterns with natbib cites.

    Three passes (order matters):
      1. Parenthetical group `(arXiv:A, arXiv:B, ...)` → `\\citep{a,b,...}`.
         Without this, three adjacent \\citep produce nested parens
         "((X), (Y), (Z))".
      2. Sentence-initial `arXiv:N` (start of paragraph or after `. `,
         `? `, `! `) → \\citet{a} so it reads "Berg et al. (2025) reports
         that..." instead of the awkward "(Berg et al., 2025) reports
         that...".
      3. Anything else → \\citep{a} (mid-sentence parenthetical).

    Required because the bibliography uses plainnat.bst, whose
    `\\bibitem[short(year)long]{key}` alias only renders correctly
    through natbib commands; bare `\\cite{}` dumps the alias verbatim.
    """
    def _bibkey(arxiv_id: str) -> str:
        return f"arxiv{arxiv_id.replace('.', '')}"

    def _grouped(m: re.Match) -> str:
        ids = re.findall(r"arXiv:(\d{4}\.\d{4,5})", m.group(1))
        keys = [_bibkey(i) for i in ids if _bibkey(i) in refs]
        if len(keys) != len(ids) or not keys:
            return m.group(0)
        return f"\\citep{{{','.join(keys)}}}"
    text = re.sub(
        r"\(((?:arXiv:\d{4}\.\d{4,5}(?:,\s*)?)+)\)",
        _grouped, text,
    )

    def _textual(m: re.Match) -> str:
        prefix, arxiv_id = m.group(1), m.group(2)
        bk = _bibkey(arxiv_id)
        return f"{prefix}\\citet{{{bk}}}" if bk in refs else m.group(0)
    text = re.sub(
        r"(^|(?<=[.!?])\s+)arXiv:(\d{4}\.\d{4,5})",
        _textual, text, flags=re.MULTILINE,
    )

    def _arxiv(m: re.Match) -> str:
        bk = _bibkey(m.group(1))
        return f"\\citep{{{bk}}}" if bk in refs else m.group(0)
    text = re.sub(r"arXiv:(\d{4}\.\d{4,5})", _arxiv, text)
    return text


def _build_authoryear_index(refs: dict) -> dict:
    """Map (firstauthor_surname_lower, year) → bibkey for prose-citation
    rewriting. Skips corporate authors (e.g. {{arXiv:2510.21258}}) since
    those are reachable via the arXiv-ID pattern."""
    idx: dict[tuple[str, str], str] = {}
    for bibkey, bibtex in refs.items():
        m_author = re.search(r"author\s*=\s*\{(.+?)\}\s*,?\s*\n", bibtex, re.DOTALL)
        m_year = re.search(r"year\s*=\s*\{(\d+)\}", bibtex)
        if not m_author or not m_year:
            continue
        author_field = m_author.group(1).strip()
        if author_field.startswith("{{") or author_field.lower() == "anonymous":
            continue  # corporate / unknown — handled via arXiv ID elsewhere
        first_chunk = author_field.split(" and ")[0].strip()
        if "," in first_chunk:
            first_lastname = first_chunk.split(",")[0].strip()
        else:
            words = first_chunk.split()
            first_lastname = words[-1] if words else first_chunk
        idx[(first_lastname.lower(), m_year.group(1))] = bibkey
    return idx


def _replace_authoryear_citations(text: str, refs: dict) -> str:
    """Rewrite prose-style author-year citations as natbib commands.

    Recognized forms (longest match first):
      1. Grouped parenthetical with `;` separators:
            (Smith et al., 2023; Jones, 2024)  →  \\citep{smith2023,jones2024}
      2. Single parenthetical:
            (Smith et al., 2023)  →  \\citep{smith2023}
      3. Textual paren-year:
            Smith et al. (2023)  →  \\citet{smith2023}
      4. Bare comma-year:
            Smith et al., 2023  →  \\citet{smith2023}

    Lookup is `(first-author-surname.lower(), year) → bibkey`. Matches
    that fail the lookup are left alone — so prose mentions of names
    not in the bib (e.g. "Section 5" or "Phase 2 (2023)") don't get
    spuriously rewritten."""
    idx = _build_authoryear_index(refs)
    if not idx:
        return text

    NAME = r"[A-Z][\wÀ-ſ\-]+"
    YEAR = r"(?:19|20|21)\d{2}"
    # First-author capture; optional second-author or "et al." after.
    AUTHORS = (
        rf"({NAME})"
        rf"(?:\s+et\s+al\.?"
        rf"|\s+and\s+(?:{NAME})"
        rf"|\s+&\s+(?:{NAME}))?"
    )

    def _lookup(surname: str, year: str) -> str | None:
        return idx.get((surname.lower(), year))

    # 1. Grouped parenthetical: (X et al., 2023; Y, 2024[; ...])
    grouped_item = rf"\s*{AUTHORS}\s*,?\s*({YEAR})\s*"
    grouped_pat = rf"\(({grouped_item}(?:;{grouped_item})+)\)"

    def grouped_repl(m: re.Match) -> str:
        body = m.group(1)
        items = re.split(r";", body)
        keys: list[str] = []
        for item in items:
            mm = re.fullmatch(rf"\s*{AUTHORS}\s*,?\s*({YEAR})\s*", item)
            if not mm:
                return m.group(0)
            key = _lookup(mm.group(1), mm.group(2))
            if not key:
                return m.group(0)
            keys.append(key)
        return f"\\citep{{{','.join(keys)}}}"
    text = re.sub(grouped_pat, grouped_repl, text)

    # 2. Single parenthetical: (Author et al., 2023)
    single_paren_pat = rf"\(\s*{AUTHORS}\s*,\s*({YEAR})\s*\)"
    def single_paren_repl(m: re.Match) -> str:
        key = _lookup(m.group(1), m.group(2))
        return f"\\citep{{{key}}}" if key else m.group(0)
    text = re.sub(single_paren_pat, single_paren_repl, text)

    # 3. Textual paren-year: Author et al. (2023)
    textual_paren_pat = rf"{AUTHORS}\s+\(({YEAR})\)"
    def textual_paren_repl(m: re.Match) -> str:
        key = _lookup(m.group(1), m.group(2))
        return f"\\citet{{{key}}}" if key else m.group(0)
    text = re.sub(textual_paren_pat, textual_paren_repl, text)

    # 4. Bare comma-year (not already inside parens / citep): Author, 2023
    #    Constrained to the start of a "name+year" chunk; word-boundary
    #    after year prevents matching e.g., a "20239" sequence.
    bare_pat = rf"{AUTHORS}\s*,\s*({YEAR})\b(?!\s*[\)\d])"
    def bare_repl(m: re.Match) -> str:
        key = _lookup(m.group(1), m.group(2))
        return f"\\citet{{{key}}}" if key else m.group(0)
    text = re.sub(bare_pat, bare_repl, text)

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

    # Run the abstract through the same conversion chain as the body.
    # Without this, raw markdown (**, %, $, _, arXiv:N citations) leaks
    # into the rendered PDF — `%` swallows the rest of its line as a
    # LaTeX comment, `**` shows up literally, etc. Stashes are
    # independent from the body's stashes; placeholders match within
    # each call.
    if abstract_body:
        abstract_body, _abs_math = _convert_math_blocks(abstract_body)
        abstract_body, _abs_code = _convert_fenced_code(abstract_body)
        abstract_body = _convert_inline_code(abstract_body)
        abstract_body = _convert_inline_emphasis(abstract_body)
        abstract_body = _convert_links(abstract_body)
        abstract_body = _replace_inline_citations(abstract_body, refs)
        abstract_body = _replace_authoryear_citations(abstract_body, refs)
        abstract_body = _escape_prose_specials(abstract_body)
        abstract_body = _restore_fenced_code(abstract_body, _abs_code)
        abstract_body = _restore_math_blocks(abstract_body, _abs_math)
    # Remove the §13 section from article_text body
    article_text = re.sub(
        r"##\s*\d+\.\s*References[\s\S]*?(?=\n##\s|\Z)",
        "",
        article_text,
    )

    # Remove the top-level "# Title\n" line and the subtitle line
    # immediately after it. The subtitle is part of the title block
    # (already in \title{...} in the preamble) and must NOT be
    # emitted as \section{} — doing so consumes section number 1
    # and shifts every subsequent section by +1 in the rendered PDF.
    article_text = re.sub(r"\A#\s+[^\n]+\n", "", article_text)
    article_text = re.sub(r"\A##\s+[^\n]+\n", "", article_text, count=1)

    # Stash math blocks ($$..$$) and fenced code blocks (```...```)
    # so they pass through every other rewrite unchanged.
    article_text, math_blocks = _convert_math_blocks(article_text)
    article_text, code_blocks = _convert_fenced_code(article_text)

    # Figures FIRST — captions can contain markdown emphasis and
    # inline-code spans whose underscores would otherwise get escaped
    # before the path could be picked up.
    article_text = _convert_figures(article_text, OUT_FIGS)

    # Footnotes: must run AFTER figure conversion so the [^id] markers
    # inside markdown captions get carried into the LaTeX caption text,
    # then replaced with \protect\footnote{} so the moving argument is safe.
    article_text = _convert_footnotes(article_text)

    # Inline patterns
    article_text = _convert_inline_code(article_text)
    article_text = _convert_inline_emphasis(article_text)
    article_text = _convert_links(article_text)
    article_text = _replace_inline_citations(article_text, refs)
    # Catch prose-style author-year mentions ("Madaan et al., 2023",
    # "Hopfield, 1982", "(Sussillo & Barak, 2013; ...)") that aren't
    # arXiv-tagged but DO have matching bib entries.
    article_text = _replace_authoryear_citations(article_text, refs)

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
