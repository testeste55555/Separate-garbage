# Schema v1.2.4 — resident-facing category QA semantics

制定日: 2026-08-19

v1.2.3の列・主キー・証拠モデルは維持し、category QAの合格意味だけを明確化する。

## category completeness

`QA_PASSED` が要求するのは、住民が家庭ごみを排出するときに選択する自治体公式の分別体系を、公式sourceとlocator付きで忠実に保持していること。

次のQA列は引き続き計算・表示するが、全自治体共通の必須TRUEとはしない。

- `危険有害`
- `収集しない物`

理由: 自治体によって、乾電池・スプレー缶・収集不可品を独立categoryにする場合と、資源ごみ等の内部品目・別ページの例外ルールとして扱う場合がある。独立categoryの存在を全自治体に強制すると、住民向け公式分類を人工的に細分化する。

## safety / excluded routes

安全性を緩和しない。乾電池、モバイルバッテリー、蛍光管、スプレー缶、ライター、家電4品目、PC等は40品目のitem mapping / coverageで個別に公式source・URL・locatorを確認する。

`APP_READY` は従来どおりITEM_SPECIFIC evidence、全条件枝COMPLETE、reviewer/dateを必須とする。

## currentness

公開日が古い公式住民向けページでも、現在も公式公開され、現年度カレンダー等が同じ分別体系の稼働を示す場合はCURRENTとして利用できる。publication ageとrule retirementを分離する。
