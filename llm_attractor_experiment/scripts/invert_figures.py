"""
Invert RGB channels of every PNG in paper/figures/ — turns black
backgrounds white and white backgrounds black, with all hues
complemented (red ↔ cyan, green ↔ magenta, blue ↔ yellow).

The original figures live under `paper/figures/fig01.png` etc. (copied
there by `scripts/build_paper_tex.py::_convert_figures`). We write the
inverted versions back to the same paths so the next pdflatex run
picks them up automatically.

Alpha channel (if any) is preserved — only RGB gets inverted.

Usage:
    # Invert in-place (overwrites paper/figures/*.png):
    python -m scripts.invert_figures

    # Write to a separate dir to compare side-by-side:
    python -m scripts.invert_figures --out paper/figures_inverted

    # Restore originals from data/* sources (re-run build_paper_tex):
    python -m scripts.build_paper_tex   # repopulates paper/figures/

Tip: the build pipeline copies figures from their source `data/<exp>/...`
locations every rebuild, so to revert after running this script, just
run `python -m scripts.build_paper_tex` again.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
FIGS = REPO / "paper" / "figures"


def invert_png(src: Path, dst: Path) -> tuple[int, int]:
    """Return (W, H) of the inverted image."""
    img = Image.open(src)
    arr = np.asarray(img)
    if arr.ndim == 2:
        # grayscale
        out = 255 - arr
    elif arr.shape[2] == 3:
        out = 255 - arr
    elif arr.shape[2] == 4:
        rgb = 255 - arr[..., :3]
        out = np.dstack([rgb, arr[..., 3:4]])
    else:
        raise RuntimeError(f"unsupported channel count {arr.shape[2]} in {src}")
    Image.fromarray(out.astype(np.uint8), mode=img.mode).save(dst)
    return arr.shape[1], arr.shape[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(FIGS))
    ap.add_argument("--out", default=None,
                    help="output dir; if omitted, overwrites in place")
    args = ap.parse_args()

    src_dir = Path(args.src)
    out_dir = Path(args.out) if args.out else src_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted(src_dir.glob("*.png"))
    if not pngs:
        print(f"no PNGs found under {src_dir}")
        return 1

    print(f"inverting {len(pngs)} figures: {src_dir} → {out_dir}")
    for p in pngs:
        w, h = invert_png(p, out_dir / p.name)
        print(f"  {p.name}  ({w}x{h})")

    print("\ndone — re-run pdflatex to pick up the inverted figures.")
    print("To revert: `python -m scripts.build_paper_tex` (re-copies originals).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
