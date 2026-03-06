# Document Normalization Rules

## source type ごとの正規化

- `openapi/json`: method/path/params/auth/errors/examples を抽出し operation 単位化
- `html`: script/style/nav を除去し endpoint パターン抽出を試行
- `markdown/text`: kind ごとに構造化（requirements, decisions, faq など）

## kind ごとの要点

- `api_spec`: endpoint / operation 単位で保存
- `project_spec`: requirements / flows / constraints / edge cases / integration notes
- `decision`: context / decision / alternatives / consequences / status
- `glossary` / `faq`: 項目単位で短く分割
- `integration_note` / `concept_note` / `troubleshooting`: decisions / todos / risks / open questions を整理

## chunking ルール

- 大文書は見出し・段落境界で分割
- 1 チャンクが過大にならないよう調整
- 断片ごとに個別 metadata を付与

## metadata 付与ルール

各 normalized 文書に以下を必ず持たせる:
`id, kind, title, project, service, source_url, source_type, last_checked, freshness, tags, related, sample_questions`

## 危険要素除去方針

- HTML の `script/style/navigation` を除去
- 明らかな命令文・プロンプト注入的文を除外
- `raw` は証跡として保存し、`normalized` は検索安全性を優先
- 出典 trace (`source_url`) を保持する
