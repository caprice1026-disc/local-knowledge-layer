#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import cache_lib


def detect_source_type(source_name: str, content: str, explicit: str | None = None) -> str:
    if explicit:
        return explicit.lower()
    suffix = Path(source_name).suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".txt"}:
        return "text"
    if suffix in {".json"}:
        return "json"
    if suffix in {".yaml", ".yml"}:
        return "openapi"
    if suffix in {".html", ".htm"}:
        return "html"
    sample = content.strip()[:2000].lower()
    if sample.startswith("{") and ("\"openapi\"" in sample or "\"swagger\"" in sample):
        return "openapi"
    if sample.startswith("{") or sample.startswith("["):
        return "json"
    if "<html" in sample:
        return "html"
    if sample.startswith("#"):
        return "markdown"
    return "text"


def _extract_keyword_lines(text: str, keywords: list[str]) -> list[str]:
    found: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip(" -*\t")
        if not line:
            continue
        lowered = line.lower()
        if any(keyword in lowered for keyword in keywords):
            found.append(line)
    return found


def _chunk_text(text: str, target: int = 1300) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n(?=#|\-|\d+\.)", text) if p.strip()]
    if not parts:
        parts = [text.strip()]
    chunks: list[str] = []
    buf: list[str] = []
    total = 0
    for part in parts:
        if total + len(part) > target and buf:
            chunks.append("\n\n".join(buf).strip())
            buf = [part]
            total = len(part)
        else:
            buf.append(part)
            total += len(part)
    if buf:
        chunks.append("\n\n".join(buf).strip())
    return [c for c in chunks if c]


def _normalize_api_html(service: str, text: str, source_url: str, freshness: str) -> list[dict[str, Any]]:
    endpoint_pattern = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/[A-Za-z0-9_./{}-]+)")
    matches = endpoint_pattern.findall(text)
    if not matches:
        matches = [("GET", "/")]
    docs: list[dict[str, Any]] = []
    for method, path in matches[:80]:
        resource_parts = [p for p in path.split("/") if p and not p.startswith("{")]
        resource = cache_lib.slugify(resource_parts[0] if resource_parts else "root", "root")
        op_slug = cache_lib.slugify(f"{method}-{path}", "operation")
        title = f"{service.upper()} {method} {path}"
        docs.append(
            {
                "metadata": {
                    "id": f"api-{cache_lib.slugify(service,'service')}-{cache_lib.slugify(method)}-{cache_lib.slugify(path)}",
                    "kind": "api_spec",
                    "title": title,
                    "project": "",
                    "service": service,
                    "source_url": source_url,
                    "source_type": "html",
                    "last_checked": cache_lib.now_iso(),
                    "freshness": freshness,
                    "tags": ["api_spec", service, method.lower(), resource],
                    "related": [],
                    "sample_questions": [
                        f"How do I call {method} {path}?",
                        f"What parameters are required for {method} {path}?",
                        f"What errors can {method} {path} return?",
                    ],
                    "version_hint": "",
                },
                "body": "\n".join(
                    [
                        f"# {title}",
                        "",
                        "## Method",
                        f"- `{method}`",
                        "",
                        "## Path",
                        f"- `{path}`",
                        "",
                        "## Summary",
                        "Extracted from HTML/docs fallback source.",
                        "",
                        "## Parameters",
                        "- verify from source docs.",
                        "",
                        "## Auth",
                        "- verify from source docs.",
                        "",
                        "## Error Model",
                        "- verify from source docs.",
                        "",
                        "## Examples",
                        "- verify from source docs.",
                    ]
                ),
                "resource": resource,
                "operation": op_slug,
            }
        )
    return docs


def normalize_source(
    *,
    kind: str,
    content: str,
    source_type: str,
    source_url: str,
    title: str,
    project: str = "",
    service: str = "",
    freshness: str = "medium",
) -> list[dict[str, Any]]:
    kind = cache_lib.ALLOWED_KINDS and kind
    if kind not in cache_lib.ALLOWED_KINDS:
        raise ValueError(f"Unsupported kind: {kind}")

    text = cache_lib.clean_html_text(content) if source_type == "html" else content

    if kind == "api_spec":
        if source_type in {"openapi", "json"}:
            spec = cache_lib.parse_openapi_text(content)
            return cache_lib.normalize_openapi_spec(spec, service=service or "service", source_url=source_url, freshness=freshness)
        return _normalize_api_html(service=service or "service", text=text, source_url=source_url, freshness=freshness)

    if kind == "project_spec":
        requirements = _extract_keyword_lines(text, ["must", "should", "require", "要件", "必須"])
        flows = _extract_keyword_lines(text, ["flow", "step", "sequence", "手順"])
        constraints = _extract_keyword_lines(text, ["constraint", "limit", "制約"])
        edges = _extract_keyword_lines(text, ["edge", "exception", "fallback", "例外"])
        integrations = _extract_keyword_lines(text, ["integration", "boundary", "api", "連携"])
        body = "\n".join(
            [
                f"# {title}",
                "",
                "## Requirements",
                "\n".join(f"- {x}" for x in requirements) if requirements else "- none extracted",
                "",
                "## Flows",
                "\n".join(f"- {x}" for x in flows) if flows else "- none extracted",
                "",
                "## Constraints",
                "\n".join(f"- {x}" for x in constraints) if constraints else "- none extracted",
                "",
                "## Edge Cases",
                "\n".join(f"- {x}" for x in edges) if edges else "- none extracted",
                "",
                "## Integration Notes",
                "\n".join(f"- {x}" for x in integrations) if integrations else "- none extracted",
            ]
        )
        return [
            {
                "metadata": {
                    "id": f"project-spec-{cache_lib.slugify(project or 'default')}-{cache_lib.slugify(title)}",
                    "kind": kind,
                    "title": title,
                    "project": project,
                    "service": service,
                    "source_url": source_url,
                    "source_type": source_type,
                    "last_checked": cache_lib.now_iso(),
                    "freshness": freshness,
                    "tags": ["project_spec", project or "default"],
                    "related": [],
                    "sample_questions": [
                        f"What requirements are defined in {project or 'this project'}?",
                        "What constraints and edge cases are documented?",
                    ],
                    "version_hint": "",
                },
                "body": body,
            }
        ]

    if kind == "decision":
        ctx = _extract_keyword_lines(text, ["context", "背景"])
        dec = _extract_keyword_lines(text, ["decision", "adopt", "採用"])
        alt = _extract_keyword_lines(text, ["alternative", "option", "却下"])
        cons = _extract_keyword_lines(text, ["impact", "consequence", "tradeoff", "影響"])
        status = _extract_keyword_lines(text, ["status", "state", "状態"])
        body = "\n".join(
            [
                f"# {title}",
                "",
                "## Context",
                "\n".join(f"- {x}" for x in ctx) if ctx else "- none extracted",
                "",
                "## Decision",
                "\n".join(f"- {x}" for x in dec) if dec else "- none extracted",
                "",
                "## Alternatives",
                "\n".join(f"- {x}" for x in alt) if alt else "- none extracted",
                "",
                "## Consequences",
                "\n".join(f"- {x}" for x in cons) if cons else "- none extracted",
                "",
                "## Status",
                "\n".join(f"- {x}" for x in status) if status else "- unknown",
            ]
        )
        return [
            {
                "metadata": {
                    "id": f"decision-{cache_lib.slugify(project or 'global')}-{cache_lib.slugify(title)}",
                    "kind": kind,
                    "title": title,
                    "project": project,
                    "service": service,
                    "source_url": source_url,
                    "source_type": source_type,
                    "last_checked": cache_lib.now_iso(),
                    "freshness": freshness,
                    "tags": ["decision", project or "global"],
                    "related": [],
                    "sample_questions": [
                        f"Why was this decision adopted in {project or 'this context'}?",
                        "What alternatives were rejected?",
                    ],
                    "version_hint": "",
                },
                "body": body,
            }
        ]

    if kind in {"glossary", "faq"}:
        entries: list[tuple[str, str]] = []
        for line in [ln.strip() for ln in text.splitlines() if ln.strip()]:
            if ":" in line:
                left, right = line.split(":", 1)
                key = left.strip(" -*")
                val = right.strip()
                if key and val:
                    entries.append((key, val))
        if not entries:
            entries = [(f"{kind}-1", _chunk_text(text)[0] if _chunk_text(text) else text.strip())]
        docs: list[dict[str, Any]] = []
        for key, val in entries:
            title_i = f"{kind.upper()} {key}"
            docs.append(
                {
                    "metadata": {
                        "id": f"{kind}-{cache_lib.slugify(project or service or 'global')}-{cache_lib.slugify(key)}",
                        "kind": kind,
                        "title": title_i,
                        "project": project,
                        "service": service,
                        "source_url": source_url,
                        "source_type": source_type,
                        "last_checked": cache_lib.now_iso(),
                        "freshness": freshness,
                        "tags": [kind, project or service or "global"],
                        "related": [],
                        "sample_questions": [f"What is '{key}'?"] if kind == "glossary" else [f"Q: {key}"],
                        "version_hint": "",
                    },
                    "body": f"# {title_i}\n\n## {key}\n{val}",
                }
            )
        return docs

    decisions = _extract_keyword_lines(text, ["decision", "adopt", "採用"])
    todos = _extract_keyword_lines(text, ["todo", "action", "next", "対応"])
    risks = _extract_keyword_lines(text, ["risk", "concern", "懸念"])
    questions = _extract_keyword_lines(text, ["question", "open", "未決", "確認"])
    chunks = _chunk_text(text)
    summary = chunks[0] if chunks else text.strip()
    body = "\n".join(
        [
            f"# {title}",
            "",
            "## Summary",
            summary or "No summary extracted.",
            "",
            "## Decisions",
            "\n".join(f"- {x}" for x in decisions) if decisions else "- none",
            "",
            "## Todos",
            "\n".join(f"- {x}" for x in todos) if todos else "- none",
            "",
            "## Risks",
            "\n".join(f"- {x}" for x in risks) if risks else "- none",
            "",
            "## Open Questions",
            "\n".join(f"- {x}" for x in questions) if questions else "- none",
        ]
    )
    return [
        {
            "metadata": {
                "id": f"{kind}-{cache_lib.slugify(project or service or 'global')}-{cache_lib.slugify(title)}",
                "kind": kind,
                "title": title,
                "project": project,
                "service": service,
                "source_url": source_url,
                "source_type": source_type,
                "last_checked": cache_lib.now_iso(),
                "freshness": freshness,
                "tags": [kind, "structured", project or service or "global"],
                "related": [],
                "sample_questions": [f"What decisions are in {title}?", f"What risks remain in {title}?"],
                "version_hint": "",
            },
            "body": body,
        }
    ]


def _project_subdir(kind: str) -> str:
    return {
        "project_spec": "specs",
        "decision": "decisions",
        "glossary": "glossary",
        "integration_note": "integrations",
        "faq": "faq",
        "concept_note": "notes",
        "troubleshooting": "troubleshooting",
        "api_spec": "integrations",
    }.get(kind, "notes")


def _global_subdir(kind: str) -> str:
    return {
        "project_spec": "specs",
        "decision": "decisions",
        "glossary": "glossary",
        "integration_note": "integrations",
        "faq": "faq",
        "concept_note": "concepts",
        "troubleshooting": "troubleshooting",
        "api_spec": "apis",
    }.get(kind, "notes")


def relative_path_for_doc(layer: str, kind: str, doc: dict[str, Any], project: str, service: str, idx: int) -> str:
    metadata = cache_lib.normalize_metadata(doc["metadata"])
    title_slug = cache_lib.slugify(metadata.get("title", metadata.get("id", "doc")), "doc")
    chunk_suffix = f"-{idx+1}" if idx > 0 else ""

    if layer == "project":
        project_name = cache_lib.slugify(project or metadata.get("project") or "default-project", "default-project")
        return f"knowledge/normalized/project/{project_name}/{_project_subdir(kind)}/{title_slug}{chunk_suffix}.md"
    if layer == "skills":
        service_name = cache_lib.slugify(service or metadata.get("service") or "general", "general")
        return f"knowledge/normalized/skills/{service_name}/{title_slug}{chunk_suffix}.md"
    if layer == "external":
        if kind == "api_spec":
            service_name = cache_lib.slugify(service or metadata.get("service") or "service", "service")
            resource = cache_lib.slugify(doc.get("resource") or "root", "root")
            operation = cache_lib.slugify(doc.get("operation") or title_slug, "operation")
            return f"knowledge/normalized/external/services/{service_name}/{resource}/{operation}.md"
        return f"knowledge/normalized/external/{_global_subdir(kind)}/{title_slug}{chunk_suffix}.md"
    if layer == "global":
        return f"knowledge/normalized/global/{_global_subdir(kind)}/{title_slug}{chunk_suffix}.md"
    raise ValueError(f"Unsupported layer: {layer}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize a source document into metadata-first markdown chunks.")
    parser.add_argument("--kind", required=True, choices=sorted(cache_lib.ALLOWED_KINDS))
    parser.add_argument("--input", dest="input_path")
    parser.add_argument("--url", dest="source_url")
    parser.add_argument("--content")
    parser.add_argument("--source-type")
    parser.add_argument("--title", default="normalized-doc")
    parser.add_argument("--project", default="")
    parser.add_argument("--service", default="")
    parser.add_argument("--freshness", default="medium", choices=["volatile", "medium", "stable"])
    args = parser.parse_args()

    if not any([args.input_path, args.source_url, args.content]):
        raise SystemExit("Provide one of --input, --url, or --content")

    if args.content is not None:
        content = args.content
        source_name = "inline"
    elif args.input_path:
        content = Path(args.input_path).read_text(encoding="utf-8")
        source_name = args.input_path
    else:
        req = Request(args.source_url, headers={"User-Agent": "local-knowledge-layer/1.0"})
        with urlopen(req, timeout=20) as res:
            content = res.read().decode("utf-8", errors="ignore")
        source_name = args.source_url

    source_type = detect_source_type(source_name, content, args.source_type)
    source_url = args.source_url or (Path(args.input_path).resolve().as_uri() if args.input_path else "manual://inline")
    docs = normalize_source(
        kind=args.kind,
        content=content,
        source_type=source_type,
        source_url=source_url,
        title=args.title,
        project=args.project,
        service=args.service,
        freshness=args.freshness,
    )
    print(json.dumps({"count": len(docs), "source_type": source_type, "docs": docs}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
