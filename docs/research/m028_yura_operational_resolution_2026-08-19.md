# M028 由良町 住民向け現行区分による解消

実施日: 2026-08-19

M028を `MANUAL_INDEX_REVIEW / QA_PASSED` へ変更する。

## 根拠
- PRIMARY_INDEX: 由良町公式 住民向けごみ分別案内
  - https://www.town.yura.wakayama.jp/docs/2014011700505/
  - 採用区分: 可燃ごみ / プラスチック / 不燃ごみ / 資源ごみ / 粗大ごみ
- SUPPLEMENTAL_INDEX / current-operation evidence: 広報ゆら 2026年3月号
  - https://www.town.yura.wakayama.jp/docs/2025122500014/files/202603.pdf
  - 2026年現在も可燃1/2、プラスチック、不燃、資源1/2、粗大ごみで収集運用されていることを確認する。

可燃1/2・資源1/2は地区別収集グループ差であり、分別categoryは各1区分とする。

## 一般化
本アプリのcategory completenessは、処理・資源化計画の全物質フローではなく、住民が排出時に選択する自治体公式分別区分の網羅を基準とする。

公開日の古い公式ページでも、現在も公式公開され、現年度カレンダー・広報等が同じ区分の運用を裏付ける場合はPRIMARY_INDEXとして利用できる。`publication age != rule retirement` とし、現行性は別の公式current-operation evidenceで確認する。
