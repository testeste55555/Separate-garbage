# M094 広島市 APP readiness Pilot

確認日: 2026-08-24
対象: M094 広島市・共通40品目

## 結果

- 40品目すべてを自治体公式資料へ品目別に照合した。
- 材質、汚れ、寸法、破損、電池内蔵、内容物残存等で分別先又は前処理が変わる場合を別条件枝として保持した。
- 40自治体品目pairを59条件枝で表現し、全枝を `ITEM_SPECIFIC / COMPLETE / APP_READY` とした。
- `data/research/app_readiness/m094_item_review.csv` を、公式品目表記、条件、前処理、例外、source、locator、確認者・確認日の監査表とする。
- category正本とcategory_idは変更していない。

## 主な条件分岐

- 食品トレー、弁当容器、菓子袋: 材質・汚れが除去できるかで分岐。
- 発泡スチロール: 商品保護用の容器包装か、それ以外の製品かで分岐。
- ガラス: 飲食料品等のびん、耐熱ガラス、破損ガラスで分岐。
- 刃物: 包丁類と、かみそり・カッター刃で分岐。
- 蛍光管・電球: 水銀使用製品とLED、白熱電球で分岐。
- スプレー缶: 中身を使い切った物と、中身が残る物で分岐。
- 小型家電・剪定枝: 通常収集の寸法・数量条件と条件外経路を分離。
- 家電リサイクル対象製品・家庭用パソコン: 市収集へ誤投影しない。

## 公式根拠

公式性は広島市公式ドメインと既存公式ドメイン台帳で確認した。主要根拠は次のとおり。

- [家庭ごみの正しい出し方](https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026095/1026096/1003182.html)
- [家庭ごみ分別50音事典（あ行）](https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008419.html)
- [家庭ごみ分別50音事典（か行）](https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008420.html)
- [家庭ごみ分別50音事典（さ行）](https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008421.html)
- [家庭ごみ分別50音事典（た行）](https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008422.html)
- [家庭ごみ分別50音事典（な行）](https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008423.html)
- [家庭ごみ分別50音事典（は行）](https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008424.html)
- [家庭ごみ分別50音事典（や・ら・わ行）](https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026094/1008426.html)
- [小型充電式電池の出し方](https://www.city.hiroshima.lg.jp/living/gomi-kankyo/1021277/1003072/1026095/1026096/1046707.html)

## QA / RED TEAM / Gate

- M094専用validator: PASS（40品目、59条件枝、公式9 source）
- mutation RED TEAM: 16/16 PASS
- canonical structural validation: PASS
- M094自治体単位 APP readiness: PASS
- canonical全体 `APP_READINESS_GATE`: HOLD

全体GateのHOLDは正常である。M094だけを原子的にAPP_READYへ移行し、残る131 active自治体を未確認のまま明示している。
