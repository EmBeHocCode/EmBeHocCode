#!/usr/bin/env python3
"""Activate one of the repository's complete GitHub profile themes."""

from __future__ import annotations

import argparse
from pathlib import Path


THEMES = (
    "cyber-hud",
    "neon-sakura",
    "minimal-terminal",
    "hologram-ocean",
)


def activate_theme(root: Path, theme: str) -> bool:
    source = root / "profile-themes" / theme / "README.md"
    destination = root / "README.md"
    marker = root / ".profile-theme"

    if not source.is_file():
        raise FileNotFoundError(f"Theme preset is missing: {source}")

    rendered = source.read_text(encoding="utf-8")
    marker_text = f"{theme}\n"
    changed = (
        not destination.exists()
        or destination.read_text(encoding="utf-8") != rendered
        or not marker.exists()
        or marker.read_text(encoding="utf-8") != marker_text
    )

    destination.write_text(rendered, encoding="utf-8", newline="\n")
    marker.write_text(marker_text, encoding="utf-8", newline="\n")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("theme", choices=THEMES, help="Theme preset to activate")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    changed = activate_theme(root, args.theme)
    state = "activated" if changed else "already active"
    print(f"Profile theme '{args.theme}' {state}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
