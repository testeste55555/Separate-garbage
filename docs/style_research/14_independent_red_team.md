# Style Research 独立RED TEAM

実施日: 2026-08-20
対象: Work実施後のStyle Research Pilot TOP10、および学習者UI接続契約

## 判定

- Style Schema / observation・projection分離: **PASS**
- category正本非破壊: **PASS**
- 地域variant隔離: **PASS**
- UI接続: **PASS**
- 出典メタデータ: **PASS WITH ONE CORRECTION REQUIRED**

## 独立確認した主要点

1. Style層はcategory正本、item mapping、教材グループから独立している。
2. 通常投影はCURRENT / SORT_BUCKETのcategoryのみを対象にする。
3. 同一categoryに指定袋・ポスター・カレンダー等の複数観測を保持し、UI projectionを別表で一意化している。
4. 共有指定袋色、装飾色、競合色をcategory識別用PRIMARYに昇格させない。
5. `OFFICIAL_DERIVED`のHEXは自治体公式HEXではなく、公式視覚資料からの近似として明示されている。
6. `NOT_CONFIRMED`は色を空欄のまま保持し、公式色を捏造しない。
7. M098尾道市・M099福山市は地域variant対応category正本が未完成のため、style層だけで架空category_idを作らずUI接続をHOLDしている。
8. learner UIでは正式区分名を残し、色を唯一の情報手段にしない。

## 発見した修正事項: M105 廿日市市

`SS-M105-02`の公式Webページは2026年時点で現行掲載されているが、ページ内で配布されているポスター自体は「令和7年1月版」である。

Work成果物の次の表現は版を誤認させる可能性がある。

- locator: `現行ポスターPDFへの公式導線`
- note: `令和8年版の現行性確認。`

真正性上は次のように扱う。

- Webページが2026年時点で当該ポスターを継続掲載していることは、現行の公式導線として利用できる。
- ただしポスター自体を「令和8年版」とは呼ばない。
- `SS-M105-01`の色根拠は、現行公式ページからリンクされている公式ポスターに基づくものとして維持できる。
- 次回Styleデータ再生成時に、source title / locator / noteを版表記に合わせて修正する。

このメタデータ修正はM105の色判定そのものを無効化するものではないが、出典監査の精度のため必須修正とする。

## UI接続時の追加防御

- `08_style_ui_projection.csv`は追加レイヤーとして読み込み、取得失敗時もcategory正本の白地ボックス表示を維持する。
- `OFFICIAL_CONFIRMED` / `OFFICIAL_DERIVED`かつ有効な`#RRGGBB`のみ色を適用する。
- `NOT_CONFIRMED` / 未調査は中立色のままにし、アプリ標準色を暗黙に公式色として扱わない。
- CSPを弱めるinline style注入は行わず、同一オリジンの既存CSSへ検証済みルールをCSSOMで追加する。
- municipality_id / category_idを安全なID形式へ限定してからselectorを生成する。
- 長い正式区分名は文字サイズのみ調整し、名称自体は省略・改名しない。

## 結論

`STYLE_UI_CONNECTION=PASS`

`NEXT_STYLE_BATCH_GATE`の方法論上のPASSは維持できる。ただしM105の版メタデータは次回再生成前に修正する。
