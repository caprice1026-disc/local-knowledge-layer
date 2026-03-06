# Architecture

## 全体アーキテクチャ

本 Skill は「常駐マルチエージェント」ではなく、必要時に CLI スクリプトを呼ぶローカル知識レイヤーとして動作する。

- `scripts/`: 取得・正規化・検索・更新の実行レイヤー
- `knowledge/raw/`: 取得元の原本保存
- `knowledge/normalized/`: 検索用に粒度調整した Markdown
- `index/knowledge.db`: SQLite FTS5 インデックス
- `manifests/`: ソース台帳と refresh 実行履歴

## Cache Hierarchy

検索優先順は固定で以下。

1. `project`
2. `skills`
3. `external / global`
4. `web`（ローカル未ヒット時のみ）

## raw / normalized / index の関係

1. 取得結果を `raw` に保存
2. `normalize_doc.py` で知識種別ごとに正規化し `normalized` に保存
3. `build_index.py` で `normalized` から `index/knowledge.db` を再構築

`index` は再生成可能な派生データとして扱う。

## 検索フロー

`search_cache.py` は FTS5 を使い、階層順に上位 N 件を取得する。返却はスニペット中心とし、全文返却を避ける。

## 更新フロー

`refresh_cache.py` は `manifests/sources.json` を読み、TTL 判定後に ETag / Last-Modified / version hint を比較する。変更ありのみ再取り込みし、最後にインデックスを再構築する。
