# Stage A後 Schema修正記録

## 当初候補からの変更

当初候補の1行表へ、次を追加・正規化した。

1. `style_id`を主キー化し、同一categoryの複数色を許可。
2. `evidence_role`で袋・容器・看板・カレンダー・ガイドを分離。
3. `official_color_label`を追加。色名確認と数値HEX確認を混同しない。
4. `semantic_fit`を追加。共有色・装飾色・競合色をcategory識別色から分離。
5. `ui_selection`を追加。公式観測を保存しても自動採用しない。
6. 観測表と`08_style_ui_projection.csv`を分離。
7. `district_scope`を必須化し、M098/M099の地域sourceを正規化。
8. `border_color` / `text_color`を自治体公式値ではなくアクセシビリティ用アプリ値と明記。
9. canonical DEFERRED自治体へ架空category_idを作らない状態を正式化。

最終Schemaは `01_style_research_schema_v1.0.md` とする。Stage Bはこの修正版で実施した。
