# paper/

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
   Conjecture 1 are opened with `\begin{lemma}`, `\begin{corollary}`,
   `\begin{conjecture}`. Closing tags (`\end{lemma}` etc.) need to
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
   `\autoref{sec:5.5}` and add `\label{sec:5.5}` to the
   `\subsection{}` line.

Re-run `python -m scripts.build_paper_tex` after editing ARTICLE.md
to regenerate.
