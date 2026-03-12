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


def _read_source(args: argparse.Namespace) -> tuple[str, str, dict[str, str]]:
    headers = {"etag": "", "last_modified": "", "version_hint": ""}
    if args.content is not None:
        return args.content, "inline", headers
    if args.input_path:
        path = Path(args.input_path)
        return path.read_text(encoding="utf-8"), str(path), headers
    if args.source_url:
        req = Request(args.source_url, headers={"User-Agent": "local-knowledge-layer/1.0"})
        with urlopen(req, timeout=30) as res:
            text = res.read().decode("utf-8", errors="ignore")
            lower_headers = {k.lower(): v for k, v in dict(res.headers.items()).items()}
            headers = {
                "etag": lower_headers.get("etag", ""),
                "last_modified": lower_headers.get("last-modified", ""),
                "version_hint": lower_headers.get("x-api-version", ""),
            }
            return text, res.geturl(), headers
    raise ValueError("Provide one of --content, --input, or --url")


def _raw_extension(source_type: str) -> str:
    return {
        "openapi": "json",
        "json": "json",
        "markdown": "md",
        "text": "txt",
        "html": "html",
    }.get(source_type, "txt")


def _source_id(kind: str, layer: str, source_url: str, project: str, service: str, source_type: str) -> str:
    seed = "|".join([kind, layer, source_url, project, service, source_type])
    return f"src-{cache_lib.slugify(kind,'kind')}-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _load_sources(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"sources": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"sources": []}


def _upsert_source(path: Path, entry: dict[str, Any]) -> None:
    payload = _load_sources(path)
    sources = payload.get("sources", [])
    replaced = False
    for idx, current in enumerate(sources):
        if current.get("source_id") == entry.get("source_id"):
            sources[idx] = entry
            replaced = True
            break
    if not replaced:
        sources.append(entry)
    payload["sources"] = sources
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def ingest(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    cache_lib.ensure_storage(root)

    content, source_name, remote_headers = _read_source(args)
    source_type = normalize_doc.detect_source_type(source_name, content, args.source_type)
    source_url = cache_lib.source_reference(args.input_path, args.source_url)

    docs = normalize_doc.normalize_source(
        kind=args.kind,
        content=content,
        source_type=source_type,
        source_url=source_url,
        title=args.title,
        project=args.project,
        service=args.service,
        freshness=args.freshness,
    )

    tags = cache_lib.to_list(args.tags)
    related = cache_lib.to_list(args.related)
    sample_questions = cache_lib.to_list(args.sample_questions)

    normalized_paths: list[str] = []
    for idx, doc in enumerate(docs):
        metadata = cache_lib.normalize_metadata(doc["metadata"])
        metadata["project"] = args.project or metadata.get("project", "")
        metadata["service"] = args.service or metadata.get("service", "")
        metadata["source_url"] = source_url
        metadata["source_type"] = source_type
        metadata["last_checked"] = cache_lib.now_iso()
        metadata["freshness"] = args.freshness
        metadata["tags"] = sorted(dict.fromkeys(cache_lib.to_list(metadata.get("tags")) + tags))
        metadata["related"] = sorted(dict.fromkeys(cache_lib.to_list(metadata.get("related")) + related))
        metadata["sample_questions"] = sorted(
            dict.fromkeys(cache_lib.to_list(metadata.get("sample_questions")) + sample_questions)
        )
        if remote_headers.get("version_hint"):
            metadata["version_hint"] = remote_headers["version_hint"]
        doc["metadata"] = metadata

        relative_path = normalize_doc.relative_path_for_doc(
            layer=args.layer,
            kind=args.kind,
            doc=doc,
            project=args.project,
            service=args.service,
            idx=idx,
        )
        file_path = cache_lib.write_normalized_doc(root, relative_path, metadata, doc["body"])
        normalized_paths.append(cache_lib._cache_relative_path(file_path, root))

    timestamp = cache_lib.now_iso().replace(":", "").replace("-", "")
    scope = cache_lib.slugify(args.project or args.service or "general", "general")
    raw_name = f"{timestamp}_{cache_lib.slugify(args.title,'source')}.{_raw_extension(source_type)}"
    raw_path = root / "knowledge" / "raw" / args.kind / scope / raw_name
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(content, encoding="utf-8")

    cache_lib.rebuild_index(root)

    source_entry = {
        "source_id": _source_id(args.kind, args.layer, source_url, args.project, args.service, source_type),
        "kind": args.kind,
        "layer": args.layer,
        "title": args.title,
        "project": args.project,
        "service": args.service,
        "source_url": source_url,
        "source_type": source_type,
        "last_checked": cache_lib.now_iso(),
        "freshness": args.freshness,
        "etag": remote_headers.get("etag", ""),
        "last_modified": remote_headers.get("last_modified", ""),
        "version_hint": remote_headers.get("version_hint", ""),
        "hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "raw_path": cache_lib._cache_relative_path(raw_path, root),
        "normalized_paths": normalized_paths,
        "ttl_days": cache_lib.FRESHNESS_TTL_DAYS.get(args.freshness, cache_lib.FRESHNESS_TTL_DAYS["medium"]),
    }
    _upsert_source(root / "manifests" / "sources.json", source_entry)

    return {
        "source_id": source_entry["source_id"],
        "source_type": source_type,
        "raw_path": source_entry["raw_path"],
        "normalized_paths": normalized_paths,
        "count": len(normalized_paths),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest local or remote source into raw + normalized cache and rebuild index.")
    parser.add_argument("--root", default=str(cache_lib.default_root()))
    parser.add_argument("--kind", required=True, choices=sorted(cache_lib.ALLOWED_KINDS))
    parser.add_argument("--layer", default="project", choices=["project", "skills", "external", "global"])
    parser.add_argument("--input", dest="input_path")
    parser.add_argument("--url", dest="source_url")
    parser.add_argument("--content")
    parser.add_argument("--source-type")
    parser.add_argument("--title", required=True)
    parser.add_argument("--project", default="")
    parser.add_argument("--service", default="")
    parser.add_argument("--freshness", default="medium", choices=["volatile", "medium", "stable"])
    parser.add_argument("--tags", default="")
    parser.add_argument("--related", default="")
    parser.add_argument("--sample-questions", default="")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not any([args.input_path, args.source_url, args.content]):
        raise SystemExit("Provide one of --input, --url, or --content")
    payload = ingest(args)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
