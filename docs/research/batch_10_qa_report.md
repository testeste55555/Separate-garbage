# Batch 10 QA Report

実施日: 2026-08-19
Schema: v1.2.4
対象MASTER: M095〜M105（M102庄原市は既完了のため対象外）

## 判定

**PASS**

- active Batch 10: 7自治体
- QA_PASSED: 7/7
- DEFERRED: M098 尾道市、M099 福山市、M100 府中市
- Batch structural validation: PASS
- Batch 10 RED TEAM: PASS（28 adversarial checks）
- canonical merge: PASS
- canonical structural validation: PASS
- Schema v1.2.4 RED TEAM: PASS
- NEXT_BATCH_GATE: PASS
- APP_READINESS_GATE: HOLD

CI記録: `docs/research/batch_10_ci_status.txt`

## active自治体と公式葉

- M095 呉市: 7
- M096 竹原市: 5
- M097 三原市: 10（`OFFICIAL_COUNT_MATCHED`）
- M101 三次市: 9
- M103 大竹市: 12
- M104 東広島市: 11
- M105 廿日市市: 10

合計公式葉: 64。廿日市市の資源ごみ投影親を含むcategory行は65。

## DEFERRED

### M098 尾道市

令和8年度に尾道・向島・御調・因島・瀬戸田の地域別CURRENT分別ガイドが公式に併存し、住民向けcategory COREに差がある。現行municipality単位Schema/UIでは居住地域を安全に解決できないため`SCHEMA_SCOPE_LIMITATION`としてDEFERRED。

### M099 福山市

市内一般は7種分別だが、市公式が令和8年度も内海町は分別方法が異なり、沼隈町は紙類の分別方法が異なると明示。単一の市全域taxonomyを適用すると誤案内になるためDEFERRED。

### M100 府中市

生成前RED TEAMで追加検出。府中地区の収集日程表は`資源ごみ及び電池`を一つの分類として表示する一方、上下地区では`資源ごみ`の下で、

- 缶・びん・電池・金属・小型家電
- 新聞・古着・紙パック
- 雑誌・段ボール

を別収集単位として表示する。単なる収集曜日差だけでなく住民向け表示単位・正式名称に地域差があるため、M098/M099と同じ`SCHEMA_SCOPE_LIMITATION`へ変更した。

固定IDと根拠は保持し、将来`district_scope`等の地域variant解決機構を実装した際に再開できる。

## 真正性確認

- 呉市: 令和8年4月新設の`プラスチック資源`を含む7収集ラベルを現行カレンダーから採用。公式ページが「6つの大分類」と表現する別粒度を理由に数値総数を捏造せず`MANUAL_INDEX_REVIEW`とした。
- 竹原市: `もやせる物 / リサイクルする物 / 資源物 / 粗大ごみ / 有害ごみ`の5区分を保持。スプレー缶は中身を使い切り、穴あけ不要。
- 三原市: 市公式が「家庭ごみの分別方法は10分別」と明記するため、Batch 10で唯一`OFFICIAL_COUNT_MATCHED=10`。発火性・有害ごみ内部4分別を独立葉として保持。
- 三次市: 定期収集9区分のみをcategory completenessへ含め、リユース本・小型家電等の別経路を人工的な追加葉にしない。
- 大竹市: 8ステーション区分＋粗大・有害・電池類・せん定枝の4公式特殊経路＝12葉を保持。スプレー缶へ他自治体の穴あけ必須ルールを推測追加しない。
- 東広島市: `リサイクルプラ`と`その他プラ`、`危険ごみ`と`有害ごみ`、新聞と雑誌等を別区分として保持。
- 廿日市市: 6種10分別の構造を保持。`資源ごみ`を教材投影親、その下の資源(1)〜(5)を公式子葉とし親を二重計上しない。スプレー缶は穴あけ不要、PETのふた・ラベルは燃やせるごみ。

## category詳細真正性

空欄回避のための「市の指定方法で出す」「公式ルールに従う」等の汎用文を生成前に再監査した。公式資料から具体的に言えない箇所は`NOT_STATED_IN_CITED_SOURCE`へ戻し、具体的な前処理が確認できる箇所だけを記録した。

## canonical更新

Batch 10統合後:

- canonical municipalities: 99
- QA: 99/99 `QA_PASSED`
- category: 1,159行
- structured official leaves: 1,072
- sources: 270
- initial mapping branches: 990
- coverage: 3,960 pair
- category review evidence: 233
- DEFERRED: 6（M065・M076・M086・M098・M099・M100）
- active implementation targets: 137

Batch 11へ進行可能。
