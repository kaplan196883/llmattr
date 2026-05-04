"""4PL fit on persistence dose-response, per observable.

Question this answers: given the observed plateau pattern, at what dose
(if any) does persistent escape cross 50%? Fit a 4-parameter logistic
to each observable's dose-response; report the upper asymptote and the
extrapolated ED50_persist (or its non-existence).

Output:
  data/aggregated/multi_observable_persistence/extrapolation.csv
  data/aggregated/multi_observable_persistence/extrapolation.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT_DIR = DATA / "aggregated" / "multi_observable_persistence"
LONG_CSV = OUT_DIR / "long.csv"

OBSERVABLES = ["output", "rolling_k3", "context_tail"]


def four_pl(x, ceiling, slope, midpoint, floor):
    """4PL: y(0) = floor; y(inf) = ceiling; midpoint = ED50; slope = Hill coef.
    y(x) = ceiling + (floor - ceiling) / (1 + (x/midpoint)**slope)
    """
    return ceiling + (floor - ceiling) / (1.0 + (x / midpoint) ** slope)


def fit_one(sub: pd.DataFrame) -> dict:
    x = sub["dose"].to_numpy(dtype=float)
    y = sub["pct_persisted"].to_numpy(dtype=float)
    p0 = (min(1.0, float(y.max()) + 0.05),  # ceiling
          1.0,                              # slope
          float(np.median(x)),              # midpoint
          max(0.0, float(y.min()) - 0.02))  # floor
    bounds = ((0.05, 0.1, 1.0, 0.0),
              (1.0, 6.0, 5000.0, 0.5))
    try:
        popt, pcov = curve_fit(four_pl, x, y, p0=p0, bounds=bounds, maxfev=20000)
    except Exception as e:
        return {"converged": False, "error": str(e),
                "ceiling": np.nan, "slope": np.nan, "midpoint": np.nan, "floor": np.nan,
                "ed50_persist": np.nan}
    ceiling, slope, midpoint, floor = popt
    perr = np.sqrt(np.maximum(0.0, np.diag(pcov)))
    # ED50_persist: smallest x where 4PL(x) = 0.5
    if ceiling < 0.5:
        ed50 = np.inf  # plateau is below threshold; threshold never reached
    elif floor > 0.5:
        ed50 = 0.0  # already above threshold at zero dose
    else:
        # 0.5 = ceiling + (floor - ceiling) / (1 + (x/midpoint)^slope)
        # (1 + (x/midpoint)^slope) = (floor - ceiling) / (0.5 - ceiling)
        # (x/midpoint)^slope = (floor - ceiling)/(0.5 - ceiling) - 1
        ratio = (floor - ceiling) / (0.5 - ceiling) - 1.0
        if ratio <= 0:
            ed50 = np.inf
        else:
            ed50 = midpoint * (ratio ** (1.0 / slope))
    return {
        "converged": True,
        "ceiling": ceiling, "slope": slope, "midpoint": midpoint, "floor": floor,
        "ceiling_se": perr[0], "slope_se": perr[1], "midpoint_se": perr[2], "floor_se": perr[3],
        "ed50_persist": ed50,
    }


def main() -> None:
    long = pd.read_csv(LONG_CSV)
    rows = []
    for obs in OBSERVABLES:
        sub = long[long["observable"] == obs].dropna(subset=["dose"]).sort_values("dose")
        fit = fit_one(sub)
        rows.append({"observable": obs, **fit})
    fits = pd.DataFrame(rows)
    out_csv = OUT_DIR / "extrapolation.csv"
    fits.to_csv(out_csv, index=False)
    print(f"wrote {out_csv}")
    print()
    print("=== 4PL fit per observable ===")
    for _, r in fits.iterrows():
        print(f"\n  observable: {r['observable']}")
        if not r["converged"]:
            print(f"    fit failed: {r['error']}")
            continue
        print(f"    ceiling (large-dose plateau) = {r['ceiling']:.3f} +/- {r['ceiling_se']:.3f}")
        print(f"    floor   (small-dose plateau) = {r['floor']:.3f} +/- {r['floor_se']:.3f}")
        print(f"    midpoint (inflection dose)   = {r['midpoint']:.1f} +/- {r['midpoint_se']:.1f}")
        print(f"    slope   (Hill coefficient)   = {r['slope']:.2f} +/- {r['slope_se']:.2f}")
        if np.isinf(r["ed50_persist"]):
            print(f"    ED50_persist                  = NEVER (ceiling {r['ceiling']:.3f} < 0.5)")
        else:
            print(f"    ED50_persist                 ~= {r['ed50_persist']:.0f} tokens "
                  f"(extrapolation; tested only up to 400)")

    # Plot fits + data
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4), sharey=True)
    obs_titles = {
        "output":       "output (single-step generation)",
        "rolling_k3":   "rolling_k3 (last 3 outputs)",
        "context_tail": "context_tail (canonical, last 4000 chars)",
    }
    xfit = np.geomspace(5, 10000, 400)
    for ax, obs in zip(axes, OBSERVABLES):
        sub = long[long["observable"] == obs].dropna(subset=["dose"]).sort_values("dose")
        x = sub["dose"].to_numpy(dtype=float)
        y = sub["pct_persisted"].to_numpy(dtype=float)
        lo = sub["persisted_ci_lo"].to_numpy(dtype=float)
        hi = sub["persisted_ci_hi"].to_numpy(dtype=float)
        fit = fits[fits["observable"] == obs].iloc[0]

        ax.errorbar(x, y, yerr=[y - lo, hi - y], fmt="o", color="#d62728",
                    markersize=6, capsize=3, label="persisted (Wilson 95% CI)")

        if fit["converged"]:
            yfit = four_pl(xfit, fit["ceiling"], fit["slope"], fit["midpoint"], fit["floor"])
            ax.plot(xfit, yfit, "-", color="#1f77b4", lw=1.6,
                    label=f"4PL fit (ceiling={fit['ceiling']:.2f})")
            ax.axhline(fit["ceiling"], color="#1f77b4", linestyle="--", lw=0.7, alpha=0.6)

        ax.axhline(0.5, color="grey", linestyle=":", lw=0.9, zorder=0,
                   label="50% half-effect threshold")
        ax.axvspan(5, 400, alpha=0.07, color="green",
                   label="tested range")
        ax.set_xscale("log")
        ax.set_xlim(5, 10000)
        ax.set_ylim(0, 1.02)
        ax.set_xlabel("adversarial dose (tokens)")
        ax.set_title(obs_titles[obs], fontsize=10)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if obs == "output":
            ax.set_ylabel("persistent-escape rate")
        ax.legend(fontsize=8, loc="upper left")

    fig.suptitle(
        "Extrapolating persistence dose-response: 4PL fit per observable\n"
        "Tested doses 20-400 tokens; fits extrapolated to 10000 tokens; ceiling = upper asymptote",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    out_png = OUT_DIR / "extrapolation.png"
    fig.savefig(out_png, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"\nwrote {out_png}")


if __name__ == "__main__":
    main()
