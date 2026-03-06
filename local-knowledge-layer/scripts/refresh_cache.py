#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.request import Request, urlopen

import cache_lib
from ingest_source import ingest, _load_sources, _upsert_source
from harvest_api_docs import harvest


def _fetch_remote_meta(url: str) -> dict[str, str]:
    req = Request(url, method="HEAD", headers={"User-Agent": "local-knowledge-layer/1.0"})
    try:
        with urlopen(req, timeout=20) as res:
            headers = {k.lower(): v for k, v in dict(res.headers.items()).items()}
            return {
                "etag": headers.get("etag", ""),
                "last_modified": headers.get("last-modified", ""),
                "version_hint": headers.get("x-api-version", ""),
            }
    except Exception:
        pass

    req_get = Request(url, headers={"User-Agent": "local-knowledge-layer/1.0"})
    try:
        with urlopen(req_get, timeout=20) as res:
            headers = {k.lower(): v for k, v in dict(res.headers.items()).items()}
            return {
                "etag": headers.get("etag", ""),
                "last_modified": headers.get("last-modified", ""),
                "version_hint": headers.get("x-api-version", ""),
            }
    except Exception:
        return {"etag": "", "last_modified": "", "version_hint": ""}


def _is_changed(existing: dict[str, Any], remote: dict[str, str]) -> bool:
    comparisons = [
        (str(existing.get("etag", "")).strip(), remote.get("etag", "").strip()),
        (str(existing.get("last_modified", "")).strip(), remote.get("last_modified", "").strip()),
        (str(existing.get("version_hint", "")).strip(), remote.get("version_hint", "").strip()),
    ]

    # Any explicit mismatch means changed.
    for old, new in comparisons:
        if old and new and old != new:
            return True

    # If no remote metadata is available, conservatively refresh.
    if not any(new for _, new in comparisons):
        return True

    # Remote metadata exists and all matching known fields are equal.
    return False


def _select_sources(sources: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    ids = set(cache_lib.to_list(args.source_ids))
    for source in sources:
        if ids and source.get("source_id") not in ids:
            continue
        if args.service and source.get("service") != args.service:
            continue
        if args.kind and source.get("kind") != args.kind:
            continue
        selected.append(source)
    return selected


def refresh(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    cache_lib.ensure_storage(root)

    payload = _load_sources(root / "manifests" / "sources.json")
    sources = payload.get("sources", [])
    selected = _select_sources(sources, args)

    checked = 0
    due = 0
    updated = 0
    unchanged = 0
    skipped = 0
    errors = 0
    details: list[dict[str, Any]] = []
    touch_updates: dict[str, dict[str, str]] = {}

    for source in selected:
        checked += 1
        source_id = source.get("source_id", "")
        freshness = source.get("freshness", "medium")
        if not cache_lib.should_refresh(source.get("last_checked"), freshness, force=args.force):
            skipped += 1
            details.append({"source_id": source_id, "status": "skip_ttl"})
            continue

        due += 1
        source_url = str(source.get("source_url", ""))
        if not source_url.startswith("http"):
            unchanged += 1
            touch_updates[source_id] = {"last_checked": cache_lib.now_iso()}
            details.append({"source_id": source_id, "status": "local_source"})
            continue

        remote_meta = _fetch_remote_meta(source_url)
        if not _is_changed(source, remote_meta):
            unchanged += 1
            touch_updates[source_id] = {
                "last_checked": cache_lib.now_iso(),
                "etag": remote_meta.get("etag", source.get("etag", "")),
                "last_modified": remote_meta.get("last_modified", source.get("last_modified", "")),
                "version_hint": remote_meta.get("version_hint", source.get("version_hint", "")),
            }
            details.append({"source_id": source_id, "status": "unchanged"})
            continue

        if args.dry_run:
            details.append({"source_id": source_id, "status": "would_update"})
            continue

        try:
            if source.get("kind") == "api_spec":
                result = harvest(
                    SimpleNamespace(
                        root=str(root),
                        service=source.get("service", "service"),
                        url=source_url,
                        layer=source.get("layer", "external"),
                        project=source.get("project", ""),
                        freshness=source.get("freshness", "volatile"),
                    )
                )
            else:
                result = ingest(
                    SimpleNamespace(
                        root=str(root),
                        kind=source.get("kind"),
                        layer=source.get("layer", "project"),
                        input_path=None,
                        source_url=source_url,
                        content=None,
                        source_type=source.get("source_type", ""),
                        title=source.get("title", source.get("kind", "doc")),
                        project=source.get("project", ""),
                        service=source.get("service", ""),
                        freshness=source.get("freshness", "medium"),
                        tags=",".join(cache_lib.to_list(source.get("tags", []))),
                        related=",".join(cache_lib.to_list(source.get("related", []))),
                        sample_questions=",".join(cache_lib.to_list(source.get("sample_questions", []))),
                    )
                )
            updated += 1
            details.append({"source_id": source_id, "status": "updated", "count": result.get("count", 0)})
        except Exception as exc:
            errors += 1
            details.append({"source_id": source_id, "status": "error", "error": str(exc)})

    # Apply unchanged/local last_checked updates without overwriting newly harvested entries.
    latest_payload = _load_sources(root / "manifests" / "sources.json")
    latest_sources = latest_payload.get("sources", [])
    for source in latest_sources:
        sid = source.get("source_id")
        if sid in touch_updates:
            source.update(touch_updates[sid])
            _upsert_source(root / "manifests" / "sources.json", source)

    summary = {
        "timestamp": cache_lib.now_iso(),
        "checked": checked,
        "due": due,
        "updated": updated,
        "unchanged": unchanged,
        "skipped": skipped,
        "errors": errors,
        "details": details,
    }

    refresh_path = root / "manifests" / "refresh-state.json"
    history_payload = {"last_run": None, "history": []}
    if refresh_path.exists():
        try:
            history_payload = json.loads(refresh_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    history = history_payload.get("history", [])
    history.append(summary)
    history_payload["last_run"] = summary["timestamp"]
    history_payload["history"] = history[-50:]
    refresh_path.write_text(json.dumps(history_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Refresh cached sources based on TTL and remote metadata.")
    parser.add_argument("--root", default=str(cache_lib.default_root()))
    parser.add_argument("--source-ids", default="", help="Comma-separated source IDs")
    parser.add_argument("--service", default="")
    parser.add_argument("--kind", default="", choices=["", *sorted(cache_lib.ALLOWED_KINDS)])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    payload = refresh(args)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
