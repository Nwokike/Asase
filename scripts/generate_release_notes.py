"""Generate release_notes.md from the in-app changelog.

Single source of truth: src/core/changelog.py NOTES keyed by APP_VERSION.
The CI release job (build-all.yml body_path) consumes the output file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.changelog import notes_for


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--build", required=True)
    parser.add_argument("--output", default="release_notes.md")
    args = parser.parse_args()

    notes = notes_for(args.version)
    body = f"# Asase {args.version} (build {args.build})\n\n{notes}\n"
    Path(args.output).write_text(body, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
