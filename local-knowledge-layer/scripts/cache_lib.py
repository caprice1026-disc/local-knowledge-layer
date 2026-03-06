from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


ALLOWED_KINDS = {
    "api_spec",
    "project_spec",
    "decision",
    "glossary",
    "faq",
    "integration_note",
    "concept_note",
    "troubleshooting",
}

FRESHNESS_TTL_DAYS = {
    "volatile": 7,
    "medium": 30,
    "stable": 120,
}

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
DISCOVERY_PATHS = [
    "/openapi.json",
    "/openapi.yaml",
    "/openapi.yml",
    "/swagger.json",
    "/swagger.yaml",
    "/swagger.yml",
    "/api-docs",
    "/docs",
    "/docs/api",
    "/docs/reference",
    "/reference",
    "/developer",
    "/developers",
    "/api/openapi.json",
    "/api/v1/openapi.json",
    "/api/v3/openapi.json",
]


def default_root() -> Path:
    return Path(__file__).resolve().parents[1]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def slugify(text: str, fallback: str = "item") -> str:
    lowered = text.strip().lower()
    lowered = re.sub(r"[^\w\s/-]", "", lowered)
    lowered = lowered.replace("/", "-")
    lowered = re.sub(r"[\s_-]+", "-", lowered).strip("-")
    return lowered[:80] or fallback


def ensure_storage(root: Path | None = None) -> None:
    base = root or default_root()
    for path in [
        base / "knowledge" / "raw",
        base / "knowledge" / "normalized" / "project",
        base / "knowledge" / "normalized" / "skills",
        base / "knowledge" / "normalized" / "external" / "services",
        base / "knowledge" / "normalized" / "global",
        base / "index",
        base / "manifests",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    sources = base / "manifests" / "sources.json"
    refresh = base / "manifests" / "refresh-state.json"
    if not sources.exists():
        sources.write_text(json.dumps({"sources": []}, indent=2, ensure_ascii=False), encoding="utf-8")
    if not refresh.exists():
        refresh.write_text(json.dumps({"last_run": None, "history": []}, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def should_refresh(last_checked: str | None, freshness: str, now: datetime | None = None, force: bool = False) -> bool:
    if force:
        return True
    checked = parse_iso(last_checked)
    if checked is None:
        return True
    reference = now or datetime.now(timezone.utc)
    ttl_days = FRESHNESS_TTL_DAYS.get((freshness or "").lower(), FRESHNESS_TTL_DAYS["medium"])
    return reference - checked >= timedelta(days=ttl_days)


def normalize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    data = dict(metadata)
    data.setdefault("id", "")
    data.setdefault("kind", "concept_note")
    data.setdefault("title", "")
    data.setdefault("project", "")
    data.setdefault("service", "")
    data.setdefault("source_url", "")
    data.setdefault("source_type", "text")
    data.setdefault("last_checked", now_iso())
    data.setdefault("freshness", "medium")
    data.setdefault("version_hint", "")
    data["tags"] = to_list(data.get("tags"))
    data["related"] = to_list(data.get("related"))
    data["sample_questions"] = to_list(data.get("sample_questions"))
    return data


def to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        if value.strip().startswith("["):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(v).strip() for v in parsed if str(v).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value).strip()]


def render_frontmatter(metadata: dict[str, Any]) -> str:
    meta = normalize_metadata(metadata)
    lines = ["---"]
    for key in ["id", "kind", "title", "project", "service", "source_url", "source_type", "last_checked", "freshness", "version_hint"]:
        value = str(meta.get(key, "")).replace('"', '\\"')
        lines.append(f"{key}: \"{value}\"")
    for key in ["tags", "related", "sample_questions"]:
        lines.append(f"{key}:")
        values = to_list(meta.get(key, []))
        if not values:
            lines.append("  -")
        else:
            for value in values:
                escaped = value.replace('"', '\\"')
                lines.append(f"  - \"{escaped}\"")
    lines.append("---")
    return "\n".join(lines)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :].lstrip("\n")
    metadata: dict[str, Any] = {}
    current_list: str | None = None
    for raw_line in raw.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("  -") and current_list:
            value = line[3:].strip().strip('"')
            metadata.setdefault(current_list, []).append(value)
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            metadata[key] = value.strip('"')
            current_list = None
        else:
            metadata[key] = []
            current_list = key
    return normalize_metadata(metadata), body


def render_document(metadata: dict[str, Any], body: str) -> str:
    return f"{render_frontmatter(metadata)}\n\n{body.strip()}\n"


def write_normalized_doc(root: Path, relative_path: str, metadata: dict[str, Any], body: str) -> Path:
    ensure_storage(root)
    path = root / Path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_document(metadata, body), encoding="utf-8")
    return path.resolve()


def parse_markdown(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8").lstrip("\ufeff")
    metadata, body = parse_frontmatter(raw)
    return {
        "metadata": normalize_metadata(metadata),
        "body": body,
        "hash": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "file_path": path.resolve().as_posix(),
    }


def infer_layer(file_path: str) -> str:
    normalized = file_path.replace("\\", "/")
    if "/knowledge/normalized/project/" in normalized:
        return "project"
    if "/knowledge/normalized/skills/" in normalized:
        return "skills"
    if "/knowledge/normalized/external/" in normalized:
        return "external"
    if "/knowledge/normalized/global/" in normalized:
        return "global"
    return "unknown"


def _connect_db(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            rowid INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT UNIQUE NOT NULL,
            file_path TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            sample_questions TEXT NOT NULL,
            tags TEXT NOT NULL,
            kind TEXT NOT NULL,
            project TEXT NOT NULL,
            service TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_type TEXT NOT NULL,
            last_checked TEXT NOT NULL,
            freshness TEXT NOT NULL,
            hash TEXT NOT NULL,
            version_hint TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
            title, body, sample_questions, tags, kind, project, service,
            content='documents', content_rowid='rowid'
        )
        """
    )
    connection.execute(
        """
        CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
            INSERT INTO documents_fts(rowid, title, body, sample_questions, tags, kind, project, service)
            VALUES(new.rowid, new.title, new.body, new.sample_questions, new.tags, new.kind, new.project, new.service);
        END;
        """
    )
    connection.execute(
        """
        CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, rowid, title, body, sample_questions, tags, kind, project, service)
            VALUES('delete', old.rowid, old.title, old.body, old.sample_questions, old.tags, old.kind, old.project, old.service);
            INSERT INTO documents_fts(rowid, title, body, sample_questions, tags, kind, project, service)
            VALUES(new.rowid, new.title, new.body, new.sample_questions, new.tags, new.kind, new.project, new.service);
        END;
        """
    )
    connection.execute(
        """
        CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, rowid, title, body, sample_questions, tags, kind, project, service)
            VALUES('delete', old.rowid, old.title, old.body, old.sample_questions, old.tags, old.kind, old.project, old.service);
        END;
        """
    )
    return connection


def rebuild_index(root: Path) -> Path:
    ensure_storage(root)
    db_file = root / "index" / "knowledge.db"
    connection = _connect_db(db_file)
    try:
        connection.execute("DELETE FROM documents")
        for path in sorted((root / "knowledge" / "normalized").rglob("*.md")):
            parsed = parse_markdown(path)
            metadata = parsed["metadata"]
            connection.execute(
                """
                INSERT OR REPLACE INTO documents (
                    doc_id, file_path, title, body, sample_questions, tags, kind, project, service,
                    source_url, source_type, last_checked, freshness, hash, version_hint, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata["id"],
                    parsed["file_path"],
                    metadata["title"],
                    parsed["body"],
                    "\n".join(metadata.get("sample_questions", [])),
                    ",".join(metadata.get("tags", [])),
                    metadata["kind"],
                    metadata.get("project", ""),
                    metadata.get("service", ""),
                    metadata.get("source_url", ""),
                    metadata.get("source_type", ""),
                    metadata.get("last_checked", ""),
                    metadata.get("freshness", ""),
                    parsed["hash"],
                    metadata.get("version_hint", ""),
                    now_iso(),
                ),
            )
        connection.commit()
    finally:
        connection.close()
    return db_file.resolve()


def _snippet(body: str, query: str, limit: int = 240) -> str:
    normalized = re.sub(r"\s+", " ", body).strip()
    if not normalized:
        return ""
    q = query.lower().strip()
    low = normalized.lower()
    if q and q in low:
        idx = low.index(q)
        start = max(0, idx - 60)
        end = min(len(normalized), idx + len(q) + 120)
        return normalized[start:end][:limit]
    return normalized[:limit]


def _search_scope(connection: sqlite3.Connection, query: str, layer: str, limit: int, project: str | None) -> list[dict[str, Any]]:
    sql = """
    SELECT d.doc_id, d.file_path, d.title, d.body, d.tags, d.kind, d.project, d.service, d.source_url, d.last_checked, d.freshness,
           bm25(documents_fts, 1.2, 1.0, 0.7, 0.4, 0.2, 0.2, 0.2) AS score
    FROM documents_fts
    JOIN documents d ON d.rowid = documents_fts.rowid
    WHERE documents_fts MATCH ?
    """
    params: list[Any] = [query]
    if layer == "project":
        sql += " AND d.file_path LIKE ?"
        params.append("%/knowledge/normalized/project/%")
        if project:
            sql += " AND d.project = ?"
            params.append(project)
    elif layer == "skills":
        sql += " AND d.file_path LIKE ?"
        params.append("%/knowledge/normalized/skills/%")
    else:
        sql += " AND (d.file_path LIKE ? OR d.file_path LIKE ?)"
        params.extend(["%/knowledge/normalized/external/%", "%/knowledge/normalized/global/%"])
    sql += " ORDER BY score LIMIT ?"
    params.append(limit)
    rows = connection.execute(sql, params).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        results.append(
            {
                "doc_id": row[0],
                "file_path": row[1],
                "title": row[2],
                "snippet": _snippet(row[3], query),
                "tags": to_list(row[4]),
                "kind": row[5],
                "project": row[6],
                "service": row[7],
                "source_url": row[8],
                "last_checked": row[9],
                "freshness": row[10],
                "score": row[11],
                "layer": infer_layer(row[1]),
            }
        )
    return results


def _parse_web_results(raw_html: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for match in re.finditer(r"<a[^>]+href=\"([^\"]+)\"[^>]*>(.*?)</a>", raw_html, re.IGNORECASE | re.DOTALL):
        url = match.group(1)
        title = html.unescape(re.sub(r"<[^>]+>", " ", match.group(2))).strip()
        if not url.startswith("http") or not title:
            continue
        results.append({"url": url, "title": re.sub(r"\s+", " ", title), "snippet": ""})
    dedup: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in results:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        dedup.append(item)
    return dedup


def web_fallback_search(query: str, limit: int = 3) -> list[dict[str, str]]:
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    req = Request(url, headers={"User-Agent": "local-knowledge-layer/1.0"})
    try:
        with urlopen(req, timeout=20) as res:
            html_body = res.read().decode("utf-8", errors="ignore")
    except Exception:
        return []
    return _parse_web_results(html_body)[:limit]


def search_hierarchy(root: Path, query: str, top_n: int = 5, project: str | None = None, allow_web_fallback: bool = True) -> dict[str, Any]:
    ensure_storage(root)
    db_file = root / "index" / "knowledge.db"
    if not db_file.exists():
        rebuild_index(root)
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    connection = _connect_db(db_file)
    try:
        for layer in ["project", "skills", "external_global"]:
            if len(results) >= top_n:
                break
            scoped = _search_scope(connection, query, layer, top_n, project)
            for item in scoped:
                if item["doc_id"] in seen:
                    continue
                seen.add(item["doc_id"])
                results.append(item)
                if len(results) >= top_n:
                    break
    finally:
        connection.close()
    fallback = web_fallback_search(query, min(top_n, 5)) if allow_web_fallback and not results else []
    return {"results": results, "fallback": fallback}


def extract_spec_links(base_url: str, html_text: str) -> list[str]:
    links: list[str] = []
    for match in re.finditer(r"href=[\"']([^\"'#]+)[\"']", html_text, re.IGNORECASE):
        href = match.group(1)
        absolute = urljoin(base_url, href)
        lowered = absolute.lower()
        if lowered.endswith((".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2")):
            continue
        if "openapi" in lowered or "/api-docs" in lowered or lowered.endswith((".json", ".yaml", ".yml")):
            links.append(absolute)
            continue
        if "swagger" in lowered and lowered.endswith((".json", ".yaml", ".yml")):
            links.append(absolute)
    return sorted(dict.fromkeys(links))


def discover_api_docs(base_url: str, timeout: int = 15) -> list[dict[str, Any]]:
    if not urlparse(base_url).scheme:
        base_url = f"https://{base_url.lstrip('/')}"
    origin = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
    found: list[dict[str, Any]] = []
    seen: set[str] = set()

    for path in DISCOVERY_PATHS + [urlparse(base_url).path or "/"]:
        candidate = urljoin(origin, path)
        if candidate in seen:
            continue
        seen.add(candidate)
        req = Request(candidate, headers={"User-Agent": "local-knowledge-layer/1.0"})
        try:
            with urlopen(req, timeout=timeout) as res:
                content_type = res.headers.get("Content-Type", "")
                preview = res.read(12000).decode("utf-8", errors="ignore")
        except (URLError, HTTPError, TimeoutError, ValueError):
            continue
        low_preview = preview.lower()
        if "openapi" in low_preview or "swagger" in low_preview or candidate.lower().endswith((".json", ".yaml", ".yml")):
            found.append({"url": candidate, "type": "openapi", "score": 0.98, "source": "known_path"})
        elif "api reference" in low_preview or "swagger-ui" in low_preview or "developer" in low_preview:
            found.append({"url": candidate, "type": "docs", "score": 0.7, "source": "known_path"})
        if "text/html" in content_type.lower() or "<html" in low_preview:
            for link in extract_spec_links(candidate, preview):
                if link in seen:
                    continue
                seen.add(link)
                found.append({"url": link, "type": "spec_link", "score": 0.9, "source": "html_link"})

    found.sort(key=lambda x: x["score"], reverse=True)
    dedup: list[dict[str, Any]] = []
    recorded: set[str] = set()
    for item in found:
        if item["url"] in recorded:
            continue
        recorded.add(item["url"])
        dedup.append(item)
    return dedup[:20]


def parse_openapi_text(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    if yaml is None:
        raise ValueError("YAML OpenAPI parsing requires PyYAML. Provide JSON or install PyYAML.")
    parsed_yaml = yaml.safe_load(content)
    if not isinstance(parsed_yaml, dict):
        raise ValueError("OpenAPI content is not an object.")
    return parsed_yaml


def _format_params(params: list[dict[str, Any]]) -> str:
    if not params:
        return "- none"
    lines: list[str] = []
    for item in params:
        name = item.get("name", "unnamed")
        location = item.get("in", "unknown")
        schema_type = ""
        if isinstance(item.get("schema"), dict):
            schema_type = item["schema"].get("type", "")
        required = "required" if item.get("required") else "optional"
        lines.append(f"- `{name}` ({location}, {schema_type or 'unknown'}, {required})")
    return "\n".join(lines)


def normalize_openapi_spec(spec: dict[str, Any], service: str, source_url: str, freshness: str = "volatile") -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    info = spec.get("info", {}) if isinstance(spec.get("info"), dict) else {}
    version_hint = str(info.get("version", ""))
    paths = spec.get("paths", {}) if isinstance(spec.get("paths"), dict) else {}

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        common_params = path_item.get("parameters", []) if isinstance(path_item.get("parameters"), list) else []
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId") or f"{method}-{path}"
            summary = operation.get("summary") or operation.get("description") or "No summary provided."
            params = [item for item in common_params if isinstance(item, dict)]
            params.extend([item for item in operation.get("parameters", []) if isinstance(item, dict)] if isinstance(operation.get("parameters"), list) else [])
            responses = operation.get("responses", {}) if isinstance(operation.get("responses"), dict) else {}
            errors = [f"- `{code}`: {payload.get('description', '')}".strip() for code, payload in responses.items() if str(code).isdigit() and int(code) >= 400 and isinstance(payload, dict)]
            if not errors:
                errors = ["- no explicit error model"]
            security = operation.get("security") or spec.get("security") or []
            auth_lines: list[str] = []
            if isinstance(security, list):
                for policy in security:
                    if isinstance(policy, dict):
                        for key, scopes in policy.items():
                            if scopes:
                                auth_lines.append(f"- {key}: {', '.join(scopes)}")
                            else:
                                auth_lines.append(f"- {key}")
            if not auth_lines:
                auth_lines = ["- not specified"]

            examples: list[str] = []
            request_body = operation.get("requestBody")
            if isinstance(request_body, dict):
                content = request_body.get("content", {})
                if isinstance(content, dict):
                    for mime, payload in content.items():
                        if isinstance(payload, dict) and "example" in payload:
                            examples.append(f"- request `{mime}`: `{payload['example']}`")
            if not examples:
                examples = ["- no explicit examples"]

            safe_service = slugify(service, "service")
            resource_parts = [p for p in path.split("/") if p and not p.startswith("{")]
            resource = slugify(resource_parts[1] if len(resource_parts) > 1 else (resource_parts[0] if resource_parts else "root"), "root")
            op_slug = slugify(str(operation_id), f"{method}-{resource}")
            title = f"{service.upper()} {method.upper()} {path}"
            body = "\n".join(
                [
                    f"# {title}",
                    "",
                    "## Method",
                    f"- `{method.upper()}`",
                    "",
                    "## Path",
                    f"- `{path}`",
                    "",
                    "## Summary",
                    str(summary).strip() or "No summary provided.",
                    "",
                    "## Parameters",
                    _format_params(params),
                    "",
                    "## Auth",
                    "\n".join(auth_lines),
                    "",
                    "## Error Model",
                    "\n".join(errors),
                    "",
                    "## Examples",
                    "\n".join(examples),
                ]
            )
            docs.append(
                {
                    "metadata": {
                        "id": f"api-{safe_service}-{slugify(method)}-{slugify(path)}",
                        "kind": "api_spec",
                        "title": title,
                        "project": "",
                        "service": service,
                        "source_url": source_url,
                        "source_type": "openapi",
                        "last_checked": now_iso(),
                        "freshness": freshness,
                        "tags": [service, "api_spec", method.lower(), resource],
                        "related": [],
                        "sample_questions": [
                            f"How do I call {method.upper()} {path} on {service}?",
                            f"What parameters are required for {method.upper()} {path}?",
                            f"What errors can {method.upper()} {path} return?",
                        ],
                        "version_hint": version_hint,
                    },
                    "body": body,
                    "resource": resource,
                    "operation": op_slug,
                }
            )
    return docs
