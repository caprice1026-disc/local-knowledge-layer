#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import cache_lib


def count_docs(db_file: Path) -> int:
    if not db_file.exists():
        return 0
    connection = sqlite3.connect(db_file)
    try:
        row = connection.execute("SELECT COUNT(*) FROM documents").fetchone()
        return int(row[0]) if row else 0
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or rebuild SQLite FTS5 index from normalized docs.")
    parser.add_argument("--root", default=str(cache_lib.default_root()), help="Skill root directory")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild index from scratch (default behavior)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    cache_lib.ensure_storage(root)
    db_file = cache_lib.rebuild_index(root)
    payload = {
        "root": root.as_posix(),
        "database": db_file.as_posix(),
        "documents": count_docs(db_file),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
