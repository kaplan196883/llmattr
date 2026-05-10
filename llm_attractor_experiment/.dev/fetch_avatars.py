"""Download stylized avatars for the 10 named users from DiceBear's free
'lorelei' avatar API. PNG, 256x256, deterministic by seed. Cached locally
so we don't re-fetch.

DiceBear license: open source (MIT) for the generator; the generated
avatars are public domain. https://www.dicebear.com/licenses/
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "avatars"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NAMES = ["Maya", "Diego", "Lila", "Theo", "Marcus", "Sofia",
         "Wei", "Hannah", "Oliver", "Aiko"]
STYLE = "lorelei"
SIZE = 256
HEADERS = {"User-Agent": "llm-attractor-experiment/1.0"}


def main() -> None:
    for name in NAMES:
        out = OUT_DIR / f"{name}.png"
        if out.exists() and out.stat().st_size > 0:
            print(f"  cached {out.name} ({out.stat().st_size//1024} KB)")
            continue
        url = (f"https://api.dicebear.com/9.x/{STYLE}/png"
               f"?seed={name}&size={SIZE}&backgroundColor=transparent")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        out.write_bytes(data)
        print(f"saved {out.name} ({len(data)//1024} KB)")
    print(f"all avatars in {OUT_DIR}")


if __name__ == "__main__":
    main()
