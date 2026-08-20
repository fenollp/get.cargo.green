#!/usr/bin/env python3
"""Record the hero terminal replay by actually running the build.

Usage:
    ./record.py                 record into assets/replay.json
    ./record.py --out FILE      record somewhere else

The hero panel replays a real `cargo green install` of a real crate, at the real
speed it ran: every line carries the number of seconds after launch at which it
appeared, and app.js schedules it against a wall clock rather than a fixed delay.

Two runs are recorded, both into a throwaway CARGO_TARGET_DIR so neither can be
helped by a warm `target/`:

    plain   `cargo install`        the baseline printed in the caption
    green   `cargo green install`  the run that gets replayed

`cargo install` refuses to reinstall a package it already installed, so the
binary is uninstalled first; the plain baseline installs into a scratch --root
so it never disturbs the real one.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "assets" / "replay.json"

CRATE = "cargo-nextest"
COMMAND = ("CARGO_TARGET_DIR=$(mktemp -d) CARGOGREEN_RUNNER=none"
           " cargo green install --frozen cargo-nextest")

# Which colour each line of cargo output replays in. First match wins; app.js
# maps these to the terminal palette.
KINDS = ((r"^\s*Compiling\b", "hit"),
         (r"^\s*(Finished|Installed)\b", "ok"),
         (r"^\s*Installing\b", "run"),
         (r"^\s*$", "blank"))


def scrub(line: str) -> str:
    """Nobody's home directory belongs on the landing page."""
    home = os.path.expanduser("~")
    return line.replace(home, "$HOME") if home not in ("", "/") else line


def kind_of(line: str) -> str:
    for pattern, kind in KINDS:
        if re.match(pattern, line):
            return kind
    return "dim"


def run(cmd: list[str], env: dict) -> tuple[list[tuple[float, str]], float, int]:
    """Run cmd, returning (lines stamped with elapsed seconds, wall clock, exit code)."""
    started = time.monotonic()
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    stamped = []
    for raw in proc.stdout:
        elapsed = time.monotonic() - started
        line = scrub(raw.rstrip("\n"))
        stamped.append((round(elapsed, 3), line))
        print(f"{elapsed:8.3f}  {line}", file=sys.stderr)
    code = proc.wait()
    return stamped, time.monotonic() - started, code


def scratch_env(**extra: str) -> dict:
    return dict(os.environ, CARGO_TARGET_DIR=tempfile.mkdtemp(), **extra)


def uninstall() -> None:
    subprocess.run(["cargo", "uninstall", CRATE], stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=False)


def record(out: Path) -> None:
    print(f"baseline: cargo install --frozen {CRATE}", file=sys.stderr)
    root = tempfile.mkdtemp()
    _, plain_wall, plain_code = run(
        ["cargo", "install", "--frozen", CRATE, "--root", root], scratch_env())
    if plain_code != 0:
        raise SystemExit(f"baseline failed with exit code {plain_code}")

    print(f"\nreplay: cargo green install --frozen {CRATE}", file=sys.stderr)
    uninstall()
    lines, wall, code = run(["cargo", "green", "install", "--frozen", CRATE],
                            scratch_env(CARGOGREEN_RUNNER="none"))
    if code != 0:
        raise SystemExit(f"replay failed with exit code {code}")

    # `cargo-green --version` prints its whole banner; the first line is the version.
    banner = subprocess.run(["cargo-green", "--version"], capture_output=True,
                            text=True, check=False).stdout
    version = banner.strip().splitlines()[0] if banner.strip() else ""

    replay = {
        "command": COMMAND,
        "recorded": time.strftime("%Y-%m-%d"),
        "tool": version,
        "wall": round(wall, 3),
        "baseline_wall": round(plain_wall, 3),
        "crates": sum(1 for _, line in lines if kind_of(line) == "hit"),
        "lines": [[at, kind_of(line), line] for at, line in lines],
    }
    out.write_text(json.dumps(replay, indent=1) + "\n", encoding="utf-8")

    print(f"\nwrote {out.relative_to(ROOT)}: {replay['crates']} crates, "
          f"{wall:.2f}s vs {plain_wall:.2f}s plain", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    record(ap.parse_args().out)


if __name__ == "__main__":
    main()
