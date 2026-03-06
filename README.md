# Local Knowledge Layer Skill

このリポジトリには、コーディングエージェント向けのローカル知識キャッシュ Skill (`local-knowledge-layer/`) が含まれています。

## できること

- API仕様・プロジェクト仕様・FAQ・用語集・設計判断を `raw` + `normalized` で保存
- SQLite FTS5 (`index/knowledge.db`) で軽量全文検索
- 検索順序を `project -> skills -> external/global -> web` に固定
- `refresh_cache.py` で TTL / ETag / Last-Modified / version hint を使った鮮度確認

## 必要環境

- Python 3.11 以上（3.13 で確認）
- ネットワーク接続（`discover` / `harvest` / URL ingest を使う場合）
- 任意: `PyYAML`（YAML形式の OpenAPI を正規化する場合のみ）

### 任意依存の導入

```bash
python -m pip install pyyaml
```

## ディレクトリ構成

- `local-knowledge-layer/SKILL.md`
- `local-knowledge-layer/agents/openai.yaml`
- `local-knowledge-layer/scripts/*.py`
- `local-knowledge-layer/references/*.md`
- `local-knowledge-layer/knowledge/raw/`
- `local-knowledge-layer/knowledge/normalized/`
- `local-knowledge-layer/index/knowledge.db`
- `local-knowledge-layer/manifests/sources.json`
- `local-knowledge-layer/manifests/refresh-state.json`

## Claude Code / OpenAI Codex への導入（Skillとして）

このリポジトリを Skill 本体として使う場合は、`local-knowledge-layer/` ディレクトリを各ツールの Skill 検索パスに配置します。

### Claude Code に導入する

プロジェクト単位（推奨）:

```powershell
New-Item -ItemType Directory -Force .\.claude\skills\local-knowledge-layer | Out-Null
Copy-Item -Path .\local-knowledge-layer\* -Destination .\.claude\skills\local-knowledge-layer -Recurse -Force
```

ユーザー共通:

```powershell
New-Item -ItemType Directory -Force "$HOME\\.claude\\skills\\local-knowledge-layer" | Out-Null
Copy-Item -Path .\local-knowledge-layer\* -Destination "$HOME\\.claude\\skills\\local-knowledge-layer" -Recurse -Force
```

使い方:
- `name: local-knowledge-layer` なので `/local-knowledge-layer` で直接呼び出せます。
- `description` に一致するタスクでは自動ロードされる場合があります。

### OpenAI Codex に導入する

リポジトリ単位（推奨）:

```powershell
New-Item -ItemType Directory -Force .\.agents\skills\local-knowledge-layer | Out-Null
Copy-Item -Path .\local-knowledge-layer\* -Destination .\.agents\skills\local-knowledge-layer -Recurse -Force
```

ユーザー共通:

```powershell
New-Item -ItemType Directory -Force "$HOME\\.agents\\skills\\local-knowledge-layer" | Out-Null
Copy-Item -Path .\local-knowledge-layer\* -Destination "$HOME\\.agents\\skills\\local-knowledge-layer" -Recurse -Force
```

使い方:
- Codex は `.agents/skills`（CWD からリポジトリルートまで）と `$HOME/.agents/skills` を走査します。
- `/skills` か `$` 補完から `local-knowledge-layer` を選択して呼び出せます。
- 必要なら `~/.codex/config.toml` の `[[skills.config]]` で有効/無効を制御できます。

### 公式ドキュメント

- Claude Code Skills: <https://code.claude.com/docs/en/skills>
- OpenAI Codex Agent Skills: <https://developers.openai.com/codex/skills/>
- OpenAI Codex CLI: <https://developers.openai.com/codex/cli/>

## クイックスタート

作業ディレクトリをリポジトリルート（この README がある場所）にして実行してください。

### 1. インデックス初期化

```bash
python local-knowledge-layer/scripts/build_index.py --root local-knowledge-layer --rebuild
```

### 2. プロジェクト文書を ingest

```bash
python local-knowledge-layer/scripts/ingest_source.py \
  --root local-knowledge-layer \
  --kind project_spec \
  --layer project \
  --project demo-shop \
  --title "Checkout Spec" \
  --input path/to/spec.md \
  --freshness medium
```

### 3. API docs を discover

```bash
python local-knowledge-layer/scripts/discover_api_docs.py \
  --root local-knowledge-layer \
  --base-url https://petstore3.swagger.io
```

### 4. API docs を harvest

```bash
python local-knowledge-layer/scripts/harvest_api_docs.py \
  --root local-knowledge-layer \
  --service petstore \
  --url https://petstore3.swagger.io \
  --layer external \
  --freshness volatile
```

### 5. ローカル検索

```bash
python local-knowledge-layer/scripts/search_cache.py \
  --root local-knowledge-layer \
  --query "retry" \
  --project demo-shop \
  --top-n 5
```

### 6. 鮮度確認・更新

ドライラン:

```bash
python local-knowledge-layer/scripts/refresh_cache.py \
  --root local-knowledge-layer \
  --dry-run
```

強制更新:

```bash
python local-knowledge-layer/scripts/refresh_cache.py \
  --root local-knowledge-layer \
  --force
```

## テスト

```bash
python -m unittest discover -s local-knowledge-layer/tests -p "test_*.py" -v
```

## バリデーション

```bash
python C:\Users\Hodaka\.codex\skills\.system\skill-creator\scripts\quick_validate.py local-knowledge-layer
```

## パッケージ化

```bash
Compress-Archive -Path local-knowledge-layer\* -DestinationPath skill.zip -Force
```

## 注意点

- キャッシュ全体を一度に読まず、`search_cache.py` の上位ヒットだけを読む設計です。
- `search_cache.py` は記号付きクエリ（例: `c++`）でもエラーにならないよう FTS クエリを安全化しています。
- HTML取り込み時は script/style/nav を除去して正規化しますが、最終判断は `source_url` の原本確認を推奨します。
