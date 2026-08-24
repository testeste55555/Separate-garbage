# M104 東広島市 APP readiness Pilot

確認日: 2026-08-24  
対象: M104 東広島市・共通40品目

## 結果

- 共通40品目を東広島市の現行公式ごみブック、分別早見表、電池・小型家電・パソコン・家電4品目の個別案内へ照合した。
- 材質、プラマーク、汚れ、容器包装用途、指定袋寸法、電池内蔵、枝径等で扱いが変わる条件を63枝で保持した。
- 40/40 pair、63/63枝を `ITEM_SPECIFIC / COMPLETE / APP_READY` とした。
- `data/research/app_readiness/m104_item_review.csv` を、品目表記、条件、前処理、例外、source、locator、確認者・確認日の監査表とする。
- 既存mapping_idを保持し、追加枝だけへ安定IDを付与した。

## 公式区分と除外経路

家電4品目と家庭用パソコンを既存の「燃やせない粗大ごみ」へ誤分類しないため、公式「市が収集・処理しないごみ」を `C-M104-12 / EXCLUDED_NOTICE` として追加した。これは通常の教材SORT_BUCKETではなく参照・警告レイヤーであり、既存の住民向け11分別の公式件数には加算しない。

## 主な条件分岐

- 食品トレー・弁当容器・袋類: プラマーク、容器包装用途、汚れの除去可否。
- 発泡スチロール: 商品保護用、非容器包装、指定袋に入らない物、紙製・汚れた物。
- 紙パック・雑がみ: アルミ加工、感熱・防水加工等の再生不能条件。
- 陶磁器・ガラス・布団: 40L指定袋へ入るか。
- モバイルバッテリー・電池内蔵家電: 40L指定袋寸法、電池取外し、絶縁・表示。
- 剪定枝: 直径8cm未満、8～20cm、20cm超の3条件。
- 家電4品目・パソコン: 市収集ではなく専用リサイクル経路。

## 主要公式根拠

- [ごみ分別早見表（33～62頁）](https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p33-62.pdf)
- [小型充電式電池等の出し方](https://www.city.higashihiroshima.lg.jp/soshiki/seikatsukankyo/8/4/1/21260.html)
- [剪定枝・伐採木の出し方（23～24頁）](https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p23-24.pdf)
- [小型家電回収（25～26頁）](https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p25-26.pdf)
- [市が収集・処理しないごみ（63頁）](https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p63.pdf)
- [パソコンのリサイクル（64頁）](https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p64.pdf)
- [家電4品目の処理（65～66頁）](https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_p65-66.pdf)

## QA / RED TEAM / Gate

- M104専用validator: PASS（40品目、63条件枝、品目証拠7 source、登録済み公式14 source、除外参照1件）
- mutation RED TEAM: 22/22 PASS
- M094回帰validator / RED TEAM: PASS（16/16）
- canonical structural validation: PASS
- M104自治体単位 APP readiness: PASS
- canonical全体 `APP_READINESS_GATE`: HOLD

全体GateのHOLDは正常である。M094・M104の2自治体だけが40/40 APP_READYで、残る130 active自治体を未確認のまま明示している。
