# Batch 08 QA Report

実施日: 2026-08-19
Schema: v1.2.4
Workflow: v1.18

## 対象

active Batch 08は9自治体。

- M074 高梁市
- M075 新見市
- M077 瀬戸内市
- M078 赤磐市
- M079 真庭市
- M080 美作市
- M081 浅口市
- M082 和気町
- M083 早島町

M076備前市はactive Batch外。固定IDと公式調査履歴は保持し、`data/master/05_deferred_municipalities.csv`へ`SCHEMA_SCOPE_LIMITATION`として記録する。

## 判定

- QA_PASSED: 9/9
- Batch 08 structural validation: PASS
- Batch 08 RED TEAM: 24/24 PASS
- canonical merge: PASS
- canonical structural validation: PASS
- Schema v1.2.4 RED TEAM: 25/25 PASS
- NEXT_BATCH_GATE: PASS
- APP_READINESS_GATE: HOLD

## Batch 08追加値

- municipalities: 9
- category rows: 108
- official resident-facing leaves: 95
- sources: 20
- initial mapping branches: 80
- coverage: 360
- category review evidence: 19

## canonical累計

- municipalities: 83
- category rows: 1,018
- official leaves: 935
- sources: 236
- QA: 83/83 PASSED
- mapping branches: 877
- coverage: 3,320
- category review evidence: 199

## 重要な真正性確認

### M074 高梁市
住民向け7区分を保持。かん類のスプレー缶・ガス缶は公式案内どおり穴あけルールを保持する。

### M077 瀬戸内市
令和8年4月開始のプラスチック資源一括回収をCURRENTへ反映。

スプレー缶・カセット式ガスボンベは、旧分別資料の穴あけ記載ではなく現在の市公式火災防止案内を優先し、**安全機構を利用して中身を完全に出し切ってから金物類へ出す**をCURRENT前処理とする。現在ルールとして穴あけ必須を補作しない。

### M078 赤磐市
現行プラスチック資源へ対象製品プラスチックを含める。

### M079 真庭市
市公式が明示する家庭ごみ分別表(1)〜(16)を16公式葉として保持。生ごみ・廃食油等の別経路で公式16葉を水増ししない。

### M080 美作市
カレンダー上の投影親と詳細公式子葉を親子構造で保持。公式葉20区分。スプレー缶の穴あけ必須を保持する。

### M081 浅口市
地域によって「もえないごみ」と「不燃性粗大ごみ」の収集日の組み方が異なるが、共通の資源11品目taxonomyと混同しない。

### M082 和気町
2026-10-01開始予定の製品プラスチック拡大は`PLANNED / HIDDEN`とし、2026-08-19時点のCURRENT公式葉へ混入させない。現行スプレー缶は穴あけルールを保持する。

### M083 早島町
現行6区分を保持。指定袋に入らない大型物でも収集シールで扱う制度を、人工的な独立「粗大ごみ」categoryへ変換しない。`EXCLUDED_NOTICE`は公式葉件数へ含めない。

## M076 備前市 — DEFERRED

令和8年度時点で、市公式は以下を併存案内している。

- 資源回収ステーション設置済地区：9種23分別
- 未設置地区：旧分別体系

これは地区別の収集曜日差ではなく、住民が選ぶ分別区分そのものの差である。現Schema v1.2.4は`municipality_id × item`を基本単位とし、地区scope/variantを安全に解決できないため、どちらか片方を備前市全域のCURRENTルールとして採用しない。

再開には`scope_id / variant_id`相当、適用地域根拠、scope単位category completeness、scope×40品目mapping/coverage、UIでのscope解決が必要。

## RED TEAM中に修正した実装不具合

1. `build_batch_08.py`で、`袋・容器のルール`等の日本語CSV列名を`dict(...)`キーワード引数として使用し、Python構文エラーになっていた。production wrapperで厳密な1行修復を行い、base builderへ永続化する経路を追加した。
2. 早島町のRED TEAMが`EXCLUDED_NOTICE`までresident category name setへ含め、6公式葉＋除外告知1行を誤ってFAILにしていた。resident category集合から`EXCLUDED_NOTICE`を除外し、`counted_category_total()`と意味境界を統一した。

どちらもcategoryデータの真正性不良ではなく、生成・検査コード側の不具合だった。
