---
name: local-knowledge-layer
description: "Local knowledge cache skill for coding agents. Use it when you need to discover, ingest, normalize, search, and refresh API docs, project specs, ADRs, glossary, FAQ, and integration notes with a local-first retrieval order: project, then skills, then external or global, then web."
---

# Local Knowledge Layer

## Purpose

Manage a portable local knowledge cache without loading the full cache into context. Read only the smallest useful snippets.

## When To Use

- You need API docs for Stripe, Slack, GitHub, OpenAI, or similar services.
- You need local lookup for project specs, design decisions, glossary, FAQ, or troubleshooting notes.
- You want to avoid repeated web search and keep evidence in raw + normalized files.
- You want to refresh stale cache entries with TTL and remote metadata checks.

## Retrieval Order

1. Project cache
2. Skill cache
3. External/global cache
4. Web retrieval (only when local cache misses)

Use `scripts/search_cache.py` with `--top-n` and snippet-first output.

## Script Roles

- `scripts/discover_api_docs.py`: find OpenAPI/Swagger/docs candidates.
- `scripts/harvest_api_docs.py`: fetch API docs, store raw, normalize by operation, update manifest, rebuild index.
- `scripts/ingest_source.py`: ingest local text/markdown/json/html/openapi or inline content.
- `scripts/normalize_doc.py`: normalize by knowledge kind and source type.
- `scripts/build_index.py`: rebuild SQLite FTS5 index from normalized markdown.
- `scripts/search_cache.py`: hierarchical search with optional web fallback.
- `scripts/refresh_cache.py`: TTL + ETag/Last-Modified/version-based refresh.

## Reference Loading Rule

Keep this file focused on control flow. Load details from:

- `references/architecture.md`
- `references/cache-schema.md`
- `references/retrieval-rules.md`
- `references/update-policy.md`
- `references/doc-normalization-rules.md`

## Context Discipline

Do not dump full documents into context. Return top matches and short snippets, then open only the needed fragments.
