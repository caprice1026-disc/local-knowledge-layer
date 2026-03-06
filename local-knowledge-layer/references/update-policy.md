# Update Policy

## freshness 種別

- `volatile`: 変化が速い情報（例: API docs）
- `medium`: 外部ナレッジ一般
- `stable`: 用語集・原則・一部 decision

## TTL

デフォルト TTL（日数）:

- `volatile`: 7
- `medium`: 30
- `stable`: 120

## refresh 挙動

1. `sources.json` から対象を選択
2. TTL 期限内はスキップ
3. 期限超過は ETag / Last-Modified / version hint を比較
4. 差分ありのみ再取り込み
5. 差分なしは `last_checked` 更新のみ

## 差分更新

- `api_spec` は `harvest_api_docs.py` で再取得
- それ以外は `ingest_source.py` で再取り込み
- 再保存時は `raw` と `normalized` を更新し、ソース台帳を upsert

## 再インデックス条件

- 更新あり: `build_index.py` を実行
- dry-run: インデックス更新しない
- 破損時: `build_index.py` で再構築
