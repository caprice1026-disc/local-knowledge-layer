# ローカル知識キャッシュ Skill フル実装 ExecPlan

この ExecPlan は living document です。`Progress`、`Surprises & Discoveries`、`Decision Log`、`Outcomes & Retrospective` を作業進行に合わせて更新します。`PLANS.md`（リポジトリルート）に従って運用します。

## Purpose / Big Picture

この変更で、コーディングエージェントが API 仕様やプロジェクト仕様を毎回 Web 取得せず、必要時だけローカルキャッシュから検索・参照・更新できるようにします。ユーザーは `search_cache.py` で階層検索（project → skills → external/global → web）を実行し、`ingest_source.py` や `harvest_api_docs.py` で知識を追加し、`refresh_cache.py` で鮮度を一括確認できます。成果は実行コマンドと `skill.zip` で確認します。

## Progress

- [x] (2026-03-06 20:37 JST) `skill-creator` の `init_skill.py` で `local-knowledge-layer/` を初期化。
- [x] (2026-03-06 20:39 JST) `.agent/` を作成し、日本語 ExecPlan を作成。
- [x] (2026-03-06 20:42 JST) 実装前テスト（TDD の RED）を追加し、`cache_lib` 未実装エラーを確認。
- [x] (2026-03-06 21:02 JST) `scripts/cache_lib.py` と 7 本の CLI スクリプトを実装。
- [x] (2026-03-06 21:06 JST) `references/*.md` と `SKILL.md` を要件準拠で作成。
- [x] (2026-03-06 21:06 JST) `knowledge/`、`index/`、`manifests/` 初期雛形を生成（`build_index.py` 実行）。
- [x] (2026-03-06 21:08 JST) テストを GREEN にし、代表スクリプトを実行確認。
- [x] (2026-03-06 21:09 JST) `quick_validate.py` 実行、`skill.zip` 生成。
- [x] (2026-03-06 21:09 JST) 実測結果を本 ExecPlan の証跡へ反映し、完了記録を更新。

## Surprises & Discoveries

- Observation: 初期化直後の `scripts/` と `references/` は空で、不要サンプルファイル削除は実質不要。
  Evidence: `Get-ChildItem -Force local-knowledge-layer\scripts` と `...\references` が空出力。

- Observation: 大きすぎる単一パッチは Windows 側で失敗したため、実装を段階分割した。
  Evidence: `apply_patch` 実行時に `ファイル名または拡張子が長すぎます` が発生。

- Observation: `quick_validate.py` は Windows 既定エンコードで読むため UTF-8 BOM 付き `SKILL.md` で失敗した。
  Evidence: `UnicodeDecodeError: 'cp932' codec can't decode byte 0xef...`。

## Decision Log

- Decision: スキル名を `local-knowledge-layer` とし、リポジトリ配下（インストール先ではない）に作成。
  Rationale: ユーザー要件「GitHub で公開可能な構成をカレントディレクトリに作成」を満たすため。
  Date/Author: 2026-03-06 / Codex

- Decision: 検索基盤は SQLite FTS5 を第一実装に固定し、ベクター DB 依存を追加しない。
  Rationale: 要件の第一候補かつローカル可搬性を優先するため。
  Date/Author: 2026-03-06 / Codex

- Decision: 正規化は `normalize_doc.py` に集約し、`ingest` / `harvest` / `refresh` は同じ正規化関数を呼び出す構成にした。
  Rationale: 知識種別ルールを一元化し、挙動差分を減らすため。
  Date/Author: 2026-03-06 / Codex

- Decision: テキストファイルは UTF-8 (BOM なし) に統一し、`SKILL.md` はバリデータ互換のため ASCII 主体にした。
  Rationale: `quick_validate.py` の Windows 既定エンコード読み込みでも確実に通すため。
  Date/Author: 2026-03-06 / Codex

## Outcomes & Retrospective

主要機能を実装し、検証と ZIP 化まで完了した。`ingest` で project docs 取り込み、`discover/harvest` で OpenAPI 収穫、`search` で階層順ヒット、`refresh` で TTL / 差分判定を確認できた。運用上は HTML discovery の精度改善余地があり、将来的には docs ページ解析の厳密化を検討する。

## Context and Orientation

作業対象は `local-knowledge-layer/` ディレクトリ配下です。ここに Anthropic Custom Skill の最小必須ファイル `SKILL.md` と `agents/openai.yaml` を置き、追加で `scripts/`、`references/`、`knowledge/`、`index/`、`manifests/` を整備します。

本実装では次を定義します。

- `scripts/cache_lib.py`: 共通ロジック。正規化、メタデータ、SQLite FTS5 インデックス、manifest 更新、TTL/差分判定、Web fallback 検索補助を担当。
- `scripts/*.py`（7本）: ユースケース単位の CLI エントリ。discover/harvest/ingest/normalize/build/search/refresh を分割。
- `references/*.md`: 設計判断と運用規約。SKILL 本文は制御面に限定し、詳細規約は references に退避。

用語定義:

- raw: 取得元そのままの保存物。再正規化や追跡のために保持。
- normalized: 検索しやすい粒度に整形した Markdown。
- index: `index/knowledge.db`。normalized を FTS5 で全文検索するための SQLite DB。
- freshness: `volatile|medium|stable`。TTL 判定に使う鮮度区分。

## Plan of Work

最初に TDD の RED として、OpenAPI 正規化、インデックス検索優先順位、refresh TTL 判定、discover の HTML 解析を検証するテストを `local-knowledge-layer/tests/` に作ります。テスト実行で失敗を確認してから、`scripts/cache_lib.py` に最小実装を入れ、順に GREEN へ持っていきます。

次に 7 本の CLI を `scripts/` に作成し、共通ロジックを呼び出す構成にします。`ingest_source.py` はローカル入力・URL・手動入力を取り込み、raw 保存、normalize、index 更新までを一括実行します。`discover_api_docs.py` は既知パス探索と HTML 内 spec リンク抽出を実装し、`harvest_api_docs.py` は OpenAPI 優先、HTML fallback の収穫フローを実装します。

その後、`references/` 5 ファイルと `SKILL.md` を要件どおりに整備します。`SKILL.md` frontmatter は `name` と `description` のみとし、本文はいつ使うか、検索順序、scripts/references の参照方法に限定します。最後に `build_index.py`、`search_cache.py`、`refresh_cache.py`、`discover_api_docs.py` または `harvest_api_docs.py` を実行して証跡を採取し、`quick_validate.py` と ZIP 生成を行います。

## Concrete Steps

作業ディレクトリはリポジトリルートです。

1. RED テスト作成と失敗確認。
   実行コマンド:
   `python -m unittest discover -s local-knowledge-layer/tests -p "test_*.py" -v`
   期待結果: モジュール未実装または未定義で FAIL。

2. `scripts/cache_lib.py` 実装後、同じテストを再実行。
   期待結果: 主要テストが PASS。

3. 7 本の CLI スクリプト実装。
   実行コマンド例:
   `python local-knowledge-layer/scripts/build_index.py --rebuild`
   `python local-knowledge-layer/scripts/search_cache.py --query "payment intent" --top-n 3 --project demo`

4. 代表スクリプトの受け入れテスト。
   - `build_index.py`
   - `search_cache.py`
   - `refresh_cache.py`
   - `discover_api_docs.py`（必要なら `harvest_api_docs.py` で代替）

5. バリデーションとパッケージング。
   実行コマンド:
   `python "$CODEX_HOME/skills/.system/skill-creator/scripts/quick_validate.py" local-knowledge-layer`
   `Compress-Archive -Path local-knowledge-layer\* -DestinationPath skill.zip -Force`

## Validation and Acceptance

受け入れはユーザー要件の 10 項目に対して観測可能な結果で確認します。具体的には、`harvest_api_docs.py` で API 仕様を 1 件以上取り込み normalized を複数チャンク生成できること、`ingest_source.py` で project docs を 1 件以上取り込み検索ヒットすること、`search_cache.py` が階層順で結果を返し、ローカル不在時にのみ web fallback を提示すること、`refresh_cache.py` が TTL と ETag/Last-Modified 比較に基づく差分更新判定を出力することを確認します。

最終的に `index/knowledge.db` が生成され、`knowledge/raw` と `knowledge/normalized` が分離され、`skill.zip` が作成できれば完了です。

## Idempotence and Recovery

`build_index.py --rebuild` は再実行しても同じ normalized 入力から同じインデックスを再生成できます。`refresh_cache.py` は差分なしの場合に再保存を行わず、`last_checked` の更新だけを反映します。失敗時は `manifests/sources.json` を保持したまま再実行できます。問題が起きた場合は `index/knowledge.db` を削除して `build_index.py --rebuild` で復旧可能です。

## Artifacts and Notes

代表コマンド実行ログ（要点）:

- `python local-knowledge-layer/scripts/build_index.py --root local-knowledge-layer --rebuild`
  - `documents: 22`
- `python local-knowledge-layer/scripts/discover_api_docs.py --base-url https://petstore3.swagger.io`
  - `api/v3/openapi.json` を候補として検出
- `python local-knowledge-layer/scripts/harvest_api_docs.py --service petstore --url https://petstore3.swagger.io`
  - `raw/api_spec/petstore/...json` と operation 単位 Markdown 19 件を生成
- `python local-knowledge-layer/scripts/ingest_source.py --kind project_spec --layer project ...`
  - `knowledge/normalized/project/demo-shop/specs/checkout-spec.md` を生成
- `python local-knowledge-layer/scripts/search_cache.py --query retry --project demo-shop --top-n 3`
  - `project -> skills -> external` の順でヒット
- `python local-knowledge-layer/scripts/refresh_cache.py --service petstore --force`
  - `updated: 1, count: 19`
- `python .../quick_validate.py local-knowledge-layer`
  - `Skill is valid!`

## Interfaces and Dependencies

実装言語は Python 3 を使用します。外部依存は極力避け、標準ライブラリ中心で構成します。OpenAPI YAML 解析は `yaml` モジュールが利用可能な場合に使用し、未導入環境では JSON/OpenAPI URL を優先しつつ明示的なエラーメッセージを返します。

最終的に存在すべき主な CLI:

- `scripts/ingest_source.py`
- `scripts/discover_api_docs.py`
- `scripts/harvest_api_docs.py`
- `scripts/normalize_doc.py`
- `scripts/build_index.py`
- `scripts/search_cache.py`
- `scripts/refresh_cache.py`

更新履歴:

- 2026-03-06: 初版作成。要件を実装可能な工程に分解し、TDD と検証コマンドを明示した。
- 2026-03-06: 実装・検証結果を反映。エンコード問題対策と discovery 改善内容を追記。
