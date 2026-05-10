"""Single-frame preview of the named-users population render with avatar
strip. Picks a frame where most users are visible and one is at peak
perturbation, so we can eyeball the layout and avatar styling.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".dev"))

from youtube_user_population_3d import (  # noqa: E402
    _frame_schedule, _load_avatars, _load_user_paths, _render_frame,
    _worker_init, _compute_iso_meshes, _spline_paths,
    DATA, N_SUBSTEPS, USER_PICKS,
)
import numpy as np  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402

OUT = DATA / "aggregated" / "dip_mechanism_B" / "preview_user_population.png"


def main() -> None:
    coords, names = _load_user_paths()
    flat = coords.reshape(-1, coords.shape[-1])
    proj_flat = PCA(n_components=3, random_state=42).fit_transform(flat)
    proj = proj_flat.reshape(coords.shape[0], coords.shape[1], 3)
    pmin, pmax = proj_flat.min(axis=0), proj_flat.max(axis=0)
    pad = 0.08 * (pmax - pmin)
    bounds = (pmin - pad, pmax + pad)
    spline_xyz, sample_t = _spline_paths(proj, N_SUBSTEPS)
    n_samples = spline_xyz.shape[1]
    schedule, offsets = _frame_schedule(n_samples, len(names))
    meshes = _compute_iso_meshes(proj_flat, bounds)
    avatars = _load_avatars(names)

    # Pick a frame where ~6-7 users are in flight and one is mid-perturbation
    target = offsets[5] + 15 * N_SUBSTEPS  # user #5 (Sofia) at step 15
    print(f"target frame {target}/{len(schedule)}")

    import tempfile
    from pathlib import Path as P
    with tempfile.TemporaryDirectory() as tmp:
        _worker_init(spline_xyz, sample_t, proj_flat, bounds, schedule,
                      offsets, names, avatars, meshes, tmp)
        png = _render_frame(target)
        # Copy to OUT
        import shutil
        shutil.copyfile(png, OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
