#!/usr/bin/env python3
"""
Research Path Resolver — one authority for where a research run writes.

Every other script in this package takes an explicit directory argument and
writes wherever it is told. That makes the output location a convention the
calling model has to remember and reproduce correctly a dozen times per run.
This script turns that convention into code: resolve the run directory once,
print it, and pass the same value to every later script call.

The convention is relative to the current working directory, so switching
workspaces moves the output with it:

    <cwd>/research/<topic>_研究_<YYYYMMDD>/

The topic segment keeps its source language. An English topic stays English,
a Chinese topic stays Chinese, and mixed topics keep both — translating proper
nouns would make finished reports harder to find later.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

CONTAINER = "research"
SUFFIX = "研究"

# Characters that are invalid in Windows paths, plus the separators and shell
# metacharacters that make a directory name awkward to quote on any platform.
_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WHITESPACE = re.compile(r"\s+")
_COLLAPSE = re.compile(r"_+")
# Leading/trailing dots and spaces are legal on POSIX but rejected by Windows.
_EDGE_JUNK = " ._"


def slugify_topic(topic: str, max_length: int = 60) -> str:
    """Turn a research topic into a single safe path segment.

    Keeps CJK characters, letters, digits and hyphens; replaces runs of
    whitespace and illegal characters with a single underscore. The topic is
    never translated, because the folder should stay recognisable to whoever
    asked the question.
    """
    text = _ILLEGAL.sub("_", topic.strip())
    text = _WHITESPACE.sub("_", text)
    text = _COLLAPSE.sub("_", text)
    text = text.strip(_EDGE_JUNK)

    if len(text) > max_length:
        text = text[:max_length].rstrip(_EDGE_JUNK)

    return text


def build_folder_name(topic: str, date: datetime | None = None) -> str:
    """Compose `<topic>_研究_<YYYYMMDD>` for one research run."""
    stamp = (date or datetime.now()).strftime("%Y%m%d")
    slug = slugify_topic(topic)
    if not slug:
        slug = "untitled"
    return f"{slug}_{SUFFIX}_{stamp}"


def resolve_run_dir(
    topic: str,
    base: str | os.PathLike[str] | None = None,
    date: datetime | None = None,
    create: bool = False,
) -> Path:
    """Return the run directory, adding a numeric suffix if the name is taken.

    Two runs of the same topic on the same day must not share a directory:
    the artifact files are append-only, so a shared folder would silently mix
    evidence from two unrelated questions.
    """
    root = Path(base) if base is not None else Path.cwd()
    folder = build_folder_name(topic, date)
    target = root / CONTAINER / folder

    if create:
        candidate = target
        index = 2
        while candidate.exists():
            candidate = root / CONTAINER / f"{folder}_{index}"
            index += 1
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate

    return target


def _cmd_resolve(args: argparse.Namespace) -> None:
    date = datetime.strptime(args.date, "%Y%m%d") if args.date else None
    path = resolve_run_dir(args.topic, base=args.base, date=date, create=args.create)
    print(
        json.dumps(
            {
                "status": "ok",
                "dir": str(path),
                "relative": path.relative_to(Path(args.base) if args.base else Path.cwd()).as_posix(),
                "created": bool(args.create),
            },
            ensure_ascii=False,
        )
    )


def _cmd_slug(args: argparse.Namespace) -> None:
    print(json.dumps({"slug": slugify_topic(args.topic)}, ensure_ascii=False))


def _cmd_check(args: argparse.Namespace) -> None:
    """Verify a directory follows the convention; used by validate_report.py."""
    path = Path(args.dir).resolve()
    problems: list[str] = []

    if path.parent.name != CONTAINER:
        problems.append(f"run directory must sit inside a '{CONTAINER}/' folder, got '{path.parent.name}'")

    if not re.search(rf"_{SUFFIX}_\d{{8}}$", path.name):
        problems.append(f"run directory name must end with '_{SUFFIX}_<YYYYMMDD>', got '{path.name}'")

    if not path.is_dir():
        problems.append(f"run directory does not exist: {path}")

    print(
        json.dumps(
            {"status": "pass" if not problems else "fail", "dir": str(path), "problems": problems},
            ensure_ascii=False,
        )
    )
    sys.exit(0 if not problems else 1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="research_paths",
        description="Resolve the output directory for a deep-research run",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_resolve = sub.add_parser("resolve", help="Print the run directory for a topic")
    p_resolve.add_argument("--topic", required=True, help="Research question or topic")
    p_resolve.add_argument("--base", default=None, help="Base directory (default: current working directory)")
    p_resolve.add_argument("--date", default=None, help="Override run date as YYYYMMDD (default: today)")
    p_resolve.add_argument("--create", action="store_true", help="Create the directory, adding _2, _3 on collision")
    p_resolve.set_defaults(func=_cmd_resolve)

    p_slug = sub.add_parser("slug", help="Print only the sanitised topic segment")
    p_slug.add_argument("--topic", required=True, help="Research question or topic")
    p_slug.set_defaults(func=_cmd_slug)

    p_check = sub.add_parser("check", help="Verify a directory follows the naming convention")
    p_check.add_argument("--dir", required=True, help="Run directory to check")
    p_check.set_defaults(func=_cmd_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
