# Data Dictionary v1.2.4 amendment

## QA.危険有害
自治体category群に危険・有害・電池・蛍光管・水銀・スプレー缶・ライター等の明示があるかを示す情報列。FALSEは「自治体に危険物ルールがない」ことを意味しない。category QAの必須TRUEではない。

## QA.収集しない物
`ui_role=EXCLUDED_NOTICE` のcategoryが存在するかを示す情報列。FALSEは「収集不可品が存在しない」ことを意味しない。category QAの必須TRUEではない。

## QA_PASSED
住民向け公式分別体系の区分網羅性・正式名称・CORE詳細・公式source・参照整合性・rule_status・ui_roleが検証済みであることを示す。危険品目・収集不可品目の最終的な処理判断はitem-level APP_READYで検証する。
