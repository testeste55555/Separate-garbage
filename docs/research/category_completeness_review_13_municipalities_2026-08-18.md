# 13自治体 区分網羅性・公式目次レビュー

実施日：2026-08-18  
対象：Schema v1.2.2で `QA_REQUIRED` だった13自治体  
範囲：Pilot / Batch 01の公式区分見出し。Batch 02および40品目APP_READYレビューは対象外。

## 結果

- 13自治体すべてを `MANUAL_INDEX_REVIEW` で確定。
- 公式総数が明記されていないため `official_category_count` は空欄を維持。
- 7区分の未構造化を4自治体で補正。
- 既存2自治体の `OFFICIAL_COUNT_MATCHED` と合わせ、15/15自治体が `QA_PASSED`。
- canonicalは201区分、57公式出典、242初期mapping枝、600 coverage pair。
- `NEXT_BATCH_GATE=PASS`、`APP_READINESS_GATE=HOLD`、RED TEAM 20/20 PASS。

## 自治体別照合

| ID | 自治体 | 公式索引・見出し | reviewed count | 補正 |
|---|---|---|---:|---|
| M001 | 山田町 | [家庭ごみの正しい分け方・出し方](https://www.town.yamada.iwate.jp/fs/1/2/9/3/6/3/_/gominodashikataposter6_3.pdf) の1ページ全見出し | 14 | なし |
| M002 | 奥州市 | [ごみ・リサイクルの出し方](https://www.city.oshu.iwate.jp/soshiki/5/1051/2/3/316.html) の燃える・燃えない・リサイクル全見出しと公式リンク | 20 | 「鉄くず（衣川地域のみ）」追加 |
| M003 | 西和賀町 | [西和賀町ごみ百科](https://www.town.nishiwaga.lg.jp/material/files/group/5/0604gomihyakka.pdf) 目次P4〜11および区分見出し | 13 | 「紙パック」追加 |
| M004 | 紫波町 | [令和8年度ごみの分け方と出し方](https://www.town.shiwa.iwate.jp/kurashi/gomi/1_bunebetsu/17749649372176/) のカテゴリナビ全件 | 12 | なし |
| M005 | 石巻市 | [家庭ごみの分け方・出し方](https://www.city.ishinomaki.lg.jp/cont/10210000/1582/kateigomi-wakekata-dasikata.pdf) の1ページ全見出し | 16 | スプレー缶・ガスカートリッジ、古着・布類、紙パック、使用済小型家電を追加 |
| M006 | 大河原町 | [令和8年度一般廃棄物処理実施計画](https://www.town.ogawara.miyagi.jp/secure/1106/R8ippannhaikibutusyorizissikeikaku.pdf) P2の分別区分表とP2〜4 | 16 | 「布類」追加 |
| M007 | 加美町 | [ごみの分別収集](https://www.town.kami.miyagi.jp/soshikikarasagasu/chominka/kankyoeisei/847.html) の分別種類表と追加回収見出し | 8 | なし |
| M008 | 白鷹町 | [ごみ分別一覧](https://www.town.shirataka.lg.jp/secure/5260/bunnbetuAll.pdf) 全30ページの「ごみの区分」列 | 9 | なし |
| M009 | 大江町 | [ごみの分け方・出し方ガイド](https://www.town.oe.yamagata.jp/files/original/202403191138227511fcddfbe.pdf) 目次P1およびP1〜15 | 8 | なし |
| M011 | 大泉町 | [令和8年度図解](https://www.town.oizumi.gunma.jp/s024/kurashi/010/010/110/R8-illust-j.pdf) の1ページ全見出し | 14 | なし |
| M013 | 港区 | [資源とごみの分別ガイドブック](https://www.city.minato.tokyo.jp/documents/6284/20260604115859.pdf) 目次P3およびP4〜26 | 9 | なし |
| M030 | 米子市 | [家庭ごみの分別・出し方](https://www.city.yonago.lg.jp/1880.htm) の本文索引と「電池類、蛍光管等」2小見出し | 10 | なし |
| M094 | 広島市 | [家庭ごみの正しい出し方](https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026095/1026096/1003182.html) の公式ページ内索引 | 8 | なし |

`reviewed count` は `CURRENT` かつ非 `EXCLUDED_NOTICE` の構造化区分数である。PLANNED、家電法対象、自治体収集外の案内は、公式資料上で照合したうえで件数外とした。

## 追加区分とデータ処理

| municipality | category_id | 公式名称 | ui_role |
|---|---|---|---|
| M002 | C-M002-21 | 鉄くず（衣川地域のみ） | SORT_BUCKET |
| M003 | C-M003-14 | 紙パック | SORT_BUCKET |
| M005 | C-M005-15 | スプレー缶・ガスカートリッジ | SORT_BUCKET |
| M005 | C-M005-16 | 古着・布類 | SORT_BUCKET |
| M005 | C-M005-17 | 紙パック | SORT_BUCKET |
| M005 | C-M005-18 | 使用済小型家電 | REFERENCE_ONLY |
| M006 | C-M006-17 | 布類 | SORT_BUCKET |

石巻市の既存「有害ごみ」からスプレー缶を外し、公式ポスターの別指定袋区分へ分離した。追加後に初期mappingとcoverageをSchema v1.2.2のPositive evidence規則で再生成した。全枝は引き続き `INITIAL_REVIEW_REQUIRED` であり、品目別公式確認済みとは扱っていない。

## 検証結果

```text
PILOT_STRUCTURAL_VALIDATION_PASSED
BATCH_01_STRUCTURAL_VALIDATION_PASSED
CANONICAL_STRUCTURAL_VALIDATION_PASSED
NEXT_BATCH_GATE_PASSED
CANONICAL_APP_READINESS_GATE_HOLD
RED_TEAM_SUMMARY=20/20
SCHEMA_V12_RED_TEAM_PASSED
```

APP_READINESS_GATEのHOLD理由は15自治体すべてで40品目レビューが未完了であること。NEXT_BATCH_GATEのPASSとは独立した正常状態である。
