#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import cache_lib
import normalize_doc
from ingest_source import _source_id, _upsert_source, _load_sources  # reuse manifest helpers


def _pick_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    ordered = sorted(
        candidates,
        key=lambda item: (
            0 if item.get("type") in {"openapi", "spec_link"} else 1,
            -float(item.get("score", 0)),
        ),
    )
    return ordered[0]


def harvest(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    cache_lib.ensure_storage(root)

    base_url = args.url or f"https://{args.service}.com"
    candidates = cache_lib.discover_api_docs(base_url)
    selected = _pick_candidate(candidates)
    target_url = selected["url"] if selected else base_url

    req = Request(target_url, headers={"User-Agent": "local-knowledge-layer/1.0"})
    with urlopen(req, timeout=30) as res:
        content = res.read().decode("utf-8", errors="ignore")
        final_url = res.geturl()
        header_map = {k.lower(): v for k, v in dict(res.headers.items()).items()}

    source_type = normalize_doc.detect_source_type(final_url, content)

    docs = normalize_doc.normalize_source(
        kind="api_spec",
        content=content,
        source_type=source_type,
        source_url=final_url,
        title=f"{args.service} api",
        project=args.project,
        service=args.service,
        freshness=args.freshness,
    )

    normalized_paths: list[str] = []
    for idx, doc in enumerate(docs):
        metadata = cache_lib.normalize_metadata(doc["metadata"])
        metadata["project"] = args.project or metadata.get("project", "")
        metadata["service"] = args.service
        metadata["source_url"] = final_url
        metadata["source_type"] = source_type
        metadata["last_checked"] = cache_lib.now_iso()
        metadata["freshness"] = args.freshness
        metadata["tags"] = sorted(dict.fromkeys(cache_lib.to_list(metadata.get("tags")) + ["api_spec", args.service]))
        metadata["version_hint"] = metadata.get("version_hint") or header_map.get("x-api-version", "")
        doc["metadata"] = metadata

        relative_path = normalize_doc.relative_path_for_doc(
            layer=args.layer,
            kind="api_spec",
            doc=doc,
            project=args.project,
            service=args.service,
            idx=idx,
        )
        file_path = cache_lib.write_normalized_doc(root, relative_path, metadata, doc["body"])
        normalized_paths.append(file_path.as_posix())

    timestamp = cache_lib.now_iso().replace(":", "").replace("-", "")
    raw_name = f"{timestamp}_{cache_lib.slugify(args.service,'service')}-api.{('json' if source_type in {'openapi','json'} else 'html')}"
    raw_scope = cache_lib.slugify(args.project or args.service or "general", "general")
    raw_path = root / "knowledge" / "raw" / "api_spec" / raw_scope / raw_name
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(content, encoding="utf-8")

    cache_lib.rebuild_index(root)

    source_entry = {
        "source_id": _source_id("api_spec", args.layer, final_url, args.project, args.service, source_type),
        "kind": "api_spec",
        "layer": args.layer,
        "title": f"{args.service} api",
        "project": args.project,
        "service": args.service,
        "source_url": final_url,
        "source_type": source_type,
        "last_checked": cache_lib.now_iso(),
        "freshness": args.freshness,
        "etag": header_map.get("etag", ""),
        "last_modified": header_map.get("last-modified", ""),
        "version_hint": header_map.get("x-api-version", ""),
        "hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "raw_path": raw_path.resolve().as_posix(),
        "normalized_paths": normalized_paths,
        "ttl_days": cache_lib.FRESHNESS_TTL_DAYS.get(args.freshness, cache_lib.FRESHNESS_TTL_DAYS["volatile"]),
    }
    _upsert_source(root / "manifests" / "sources.json", source_entry)

    return {
        "service": args.service,
        "target_url": final_url,
        "source_type": source_type,
        "raw_path": source_entry["raw_path"],
        "normalized_paths": normalized_paths,
        "count": len(normalized_paths),
        "discovery_candidates": candidates,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Discover and harvest API docs/OpenAPI into cache.")
    parser.add_argument("--root", default=str(cache_lib.default_root()))
    parser.add_argument("--service", required=True)
    parser.add_argument("--url", help="Base URL or explicit docs/spec URL")
    parser.add_argument("--layer", default="external", choices=["project", "skills", "external", "global"])
    parser.add_argument("--project", default="")
    parser.add_argument("--freshness", default="volatile", choices=["volatile", "medium", "stable"])
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    payload = harvest(args)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
