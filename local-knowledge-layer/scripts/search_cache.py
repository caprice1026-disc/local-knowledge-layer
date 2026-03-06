#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cache_lib


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Search local knowledge cache with hierarchy fallback.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--project", default="")
    parser.add_argument("--root", default=str(cache_lib.default_root()))
    parser.add_argument("--no-web-fallback", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    result = cache_lib.search_hierarchy(
        root=root,
        query=args.query,
        top_n=max(1, args.top_n),
        project=args.project or None,
        allow_web_fallback=not args.no_web_fallback,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
