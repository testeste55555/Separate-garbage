#!/usr/bin/env bash
set -euo pipefail

URL="https://www.city.fukuyama.hiroshima.jp/uploaded/attachment/273294.pdf"
PDF="/tmp/m099-utsumi-guide.pdf"
TXT="/tmp/m099-utsumi-guide.txt"

curl --fail --location --silent --show-error "$URL" -o "$PDF"
pdftotext -layout "$PDF" "$TXT"

if [[ ! -s "$TXT" ]]; then
  echo "M099_UTSUMI_PDF_AUDIT_FAILED: extracted text is empty"
  exit 1
fi

# The common 40-item inventory uses these everyday labels/near-synonyms. Print
# context only; absence is not automatically treated as a negative rule.
PATTERN='ペットボトル|キャップ|ラベル|アルミ缶|スチール缶|びん|ビン|トレイ|弁当|菓子|レジ袋|発泡スチロール|新聞|段ボール|ダンボール|雑誌|紙パック|生ごみ|ティッシュ|おむつ|衣類|傘|陶磁器|ガラス|包丁|乾電池|ボタン電池|充電式電池|モバイルバッテリー|蛍光灯|電球|スプレー缶|ライター|小型家電|布団|テレビ|エアコン|冷蔵庫|洗濯機|パソコン|食用油|剪定枝|枝木'

echo "M099_UTSUMI_PDF_AUDIT_BEGIN"
grep -n -E -C 2 "$PATTERN" "$TXT" || true
echo "M099_UTSUMI_PDF_AUDIT_END"

echo "M099_UTSUMI_SECTION_HEADINGS"
grep -n -E '燃やせるごみ|容器包装プラスチックごみ|紙類|資源ごみ|不燃|燃やせる粗大ごみ|蛍光灯・使用済乾電池|市で収集しない|メーカーが行うリサイクル' "$TXT" || true
