# アプリUI HANDOFF

## 読み込み順

1. 既存正本から選択自治体の `CURRENT / SORT_BUCKET` を取得する。
2. `(municipality_id, district_scope, category_id)` で `08_style_ui_projection.csv` をLEFT JOINする。
3. `OFFICIAL_DERIVED` / `OFFICIAL_CONFIRMED` はdisplay・border・textを適用する。
4. `NOT_CONFIRMED` は空欄を維持し、必要ならアプリ側標準色を実行時に `FALLBACK` として適用する。

FALLBACKは公式style行を上書きしない。ログ・UIデバッグ表示でも公式/近似/標準を区別できる状態を保持する。

## 表示契約

- 正式区分名を常に表示する。
- 色だけを唯一の識別手段にしない。
- borderを併用する。
- 将来アイコンを加える場合も、公式sourceがない独自アイコンを公式情報列へ入れない。
- `REFERENCE_ONLY`、`HIDDEN`、`EXCLUDED_NOTICE`へ通常箱styleを適用しない。
- `display_color`が同じcategory群でも統合・改名しない。

## status別挙動

| status | UI挙動 |
|---|---|
| OFFICIAL_CONFIRMED | 公式が明示した色名/値として利用。数値が空なら名前だけで自動HEX化しない |
| OFFICIAL_DERIVED | 公式視覚資料由来の近似として利用可能。自治体公式HEXと表示しない |
| NOT_CONFIRMED | 公式色なし/一意化不可。必要ならFALLBACKを別状態で付与 |
| FALLBACK | アプリ標準色。公式色バッジや公式根拠リンクを表示しない |

## 地域variant

M098/M099は現時点でUI選択不可。将来canonicalがdistrict_scope対応した後、居住地域を確定してからstyleをjoinする。municipality_idだけで市全域styleへ丸めない。

## アクセシビリティ

Pilotの`border_color`と`text_color`は公式値ではなくアプリ計算値である。validatorで文字コントラスト4.5:1以上を確認済み。アイコン追加後も正式名称・色・枠線の冗長な手掛かりを維持する。
