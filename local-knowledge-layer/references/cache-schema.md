# Cache Schema

## ディレクトリ構成

- `knowledge/raw/`
- `knowledge/normalized/project/<project_name>/specs/`
- `knowledge/normalized/project/<project_name>/decisions/`
- `knowledge/normalized/project/<project_name>/glossary/`
- `knowledge/normalized/project/<project_name>/integrations/`
- `knowledge/normalized/skills/`
- `knowledge/normalized/external/services/`
- `knowledge/normalized/global/`
- `index/knowledge.db`
- `manifests/sources.json`
- `manifests/refresh-state.json`

## 文書粒度

- `api_spec`: endpoint / operation 単位
- `project_spec`: feature / requirement / flow / constraint 単位
- `decision`: ADR / decision 単位
- `glossary` / `faq`: 1項目または少数項目単位
- `integration_note` / `concept_note` / `troubleshooting`: 検索可能な小チャンク単位

## 命名規則

- ファイル名はスラグ化（英数字・ハイフン）
- API 仕様は `service/resource/operation.md` を優先
- metadata `id` は安定した識別子を使う

## metadata 一覧

normalized Markdown 先頭の metadata で下記を保持する。

- `id`
- `kind`
- `title`
- `project`
- `service`
- `source_url`
- `source_type`
- `last_checked`
- `freshness`
- `tags`
- `related`
- `sample_questions`
- `version_hint`

## path 規約

- `project` 層は project 名必須
- `skills` 層は service サブディレクトリを推奨
- `external` 層の API 仕様は `external/services/<service>/...`
- `global` 層は知識種別サブディレクトリに分ける
