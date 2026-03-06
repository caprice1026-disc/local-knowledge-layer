#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cache_lib


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover API docs/OpenAPI candidates from a service URL.")
    parser.add_argument("--base-url", help="Base URL to inspect")
    parser.add_argument("--service", help="Service name, converted to https://<service>.com when base-url is omitted")
    parser.add_argument("--root", default=str(cache_lib.default_root()))
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    if not args.base_url and not args.service:
        raise SystemExit("Provide --base-url or --service")

    base_url = args.base_url or f"https://{args.service}.com"
    candidates = cache_lib.discover_api_docs(base_url)
    payload = {
        "base_url": base_url,
        "count": len(candidates),
        "candidates": candidates,
    }

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
