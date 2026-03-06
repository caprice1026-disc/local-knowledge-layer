# Retrieval Rules

## 階層順

必ず次の順で検索する。

1. `project cache`
2. `skill cache`
3. `external/global cache`
4. `web retrieval`

## Top N

- デフォルトは上位 5 件
- ユースケースで `--top-n` を指定可能
- 取得量は必要最小限に絞る

## Ranking ルール

- SQLite FTS5 の `bm25` スコアを利用
- 同点時は階層優先順を維持
- 重複 `doc_id` は除外

## Snippet 方針

- 返却はタイトル + スニペット（短文）中心
- 全文返却を禁止
- クエリ近傍を優先して切り出す

## Fallback 条件

- ローカル 3 層でヒット 0 件のときのみ Web 検索
- Web 結果は候補 URL と短い要約のみ返す
- 有用なら `harvest` / `ingest` でローカルへ格納する
