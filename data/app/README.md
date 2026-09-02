# app data

Webアプリが直接読み込む加工済みデータを置くディレクトリです。

調査中の生データを直接アプリへ渡さず、QA済みデータから生成します。

想定成果物：

- `app_export.json`
- 自治体別の必要最小限の分別データ
- `lesson_item_set.csv`：授業で使用する正式15品目セット。`CORE_10`と`SUPPLEMENTAL_5`を区別し、既存`internal_item_id`だけを参照する
- `item_image_assets.csv`：教材画像と共通品目の対応表
- `item_image_mapping_pilot_top8.csv`：歴史的ファイル名を維持した、画像10品目と自治体単位scoring scope 12自治体の公式分別先台帳（120 VERIFIED / 0 UNRESOLVED）
- `lesson_mode_app_ready_scope.csv`：オンライン授業モードで自動正誤判定を有効にする`APP_READY`／`LESSON_READY_10`自治体の明示的スコープ（歴史的ファイル名を維持）
- `lesson_teaching_boxes.csv`：一般自治体のオンライン固定10品目採点BOXと対面主要分別箱を`class_mode`で分離する教材投影
- `lesson_item_scoring_projection.csv`：一般自治体の画像品目を採点BOXへ結ぶ投影。公式categoryと`SIMPLIFIED_ACTION`を明示的に区別する
- `district_scopes.csv`：地域variant自治体の公式地域範囲を保持する内部索引。学習者へ直接表示しない
- `lesson_variant_groups.csv`：固定10品目の正答差だけを基準にした学習者向け地域グループ
- `lesson_variant_teaching_boxes.csv`：地域variant用BOX。オンライン固定10品目採点用と、対面授業の主要分別箱を`class_mode`で分離する
- `lesson_variant_item_scoring.csv`：`lesson_variant_group`単位の固定10品目採点表

品目情報の正本は `data/master/04_common_items_master.csv` です。

## 授業用正式15品目セット

授業で使用する品目集合は`data/app/lesson_item_set.csv`を正本とし、次の15品目に固定します。

- `CORE_10`：I001 ペットボトル、I004 アルミ缶、I006 ガラスびん、I007 白色食品トレー、I013 新聞、I014 段ボール、I017 紙パック、I029 モバイルバッテリー、I031 電球、I033 使い捨てライター
- `SUPPLEMENTAL_5`：I002 ペットボトルのキャップ、I003 ペットボトルのラベル、I027 乾電池、I018 生ごみ、I010 お菓子の袋

この15品目セットは**授業で扱う品目集合の定義**であり、scoring readinessを変更しません。既存の`LESSON_READY_10`は引き続き`CORE_10`だけを対象とする安全Gateです。`SUPPLEMENTAL_5`を15品目セットへ含めただけでは、自治体別mapping、条件枝確認、画像登録、自動正誤判定を有効化しません。それらは別工程で公式根拠を確認して追加します。

Pilotの`VERIFIED`だけでは学習者画面の自動正誤判定を有効にしません。`branch_completeness_confirmed=TRUE`、明示的lesson scope、画像固有mappingの`VERIFIED`をすべて要求します。

オンライン授業モードで画像問題を有効にする経路は2つです。

- `APP_READY`：40共通品目の全条件枝が`COMPLETE`
- `LESSON_READY_10`：固定画像10品目の全条件枝が`COMPLETE`で、scope固定の必須枝数と一致し、各品目に画像と一致するscoring branchがちょうど1つ

後者は40品目`APP_READY`への昇格ではなく、残り30品目を未完了のまま明示します。対面授業モードでは画像問題を使用せず、固定10品目専用BOXではなく授業で必要な主要分別箱を投影します。`SIMPLIFIED_ACTION`は自治体正式区分ではなく、非通常収集品目等を通常分別BOXへ誤投影せず自動採点するための教材用簡略行動箱です。M107 I007、M110 I029、M111 I029は詳細な非通常経路をエビデンス層に保持し、学習者には「回収・確認」だけを表示します。M106 I029は現行家庭ごみルールに基づき`C-M106-12 有害ごみ`へ通常の公式categoryとして投影します。

M098尾道市・M099福山市は、完全な地域別category taxonomyを複製せず、地域variant専用層で`LESSON_READY_10`を先行します。M098は6つの内部district scopeで固定10品目の教材正答が同一であることを確認し、1つのlesson groupへ束ねるため地域選択を表示しません。M099は固定10品目の紙類正答が変わるため、一般地域／内海町・沼隈町／走島町の3択だけを表示します。内海町と沼隈町は再分割せず、走島町のフェリー・持込施設・特殊回収経路は学習者向けBOXへ追加しません。完全taxonomy・40品目`APP_READY`側の`DEFERRED`は維持します。

この領域のデータは、教師画面・学習者投映画面での利用を前提にします。
