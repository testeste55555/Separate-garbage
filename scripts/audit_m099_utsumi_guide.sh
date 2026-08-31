#!/usr/bin/env bash
set -euo pipefail

# Source roles are deliberately separated:
# - 2026 Utsumi calendar = current regional scope / collection-category authority.
# - Utsumi guide = supplemental item/preparation detail only where needed.
CALENDAR_URL="https://www.city.fukuyama.hiroshima.jp/uploaded/attachment/327009.pdf"
GUIDE_URL="https://www.city.fukuyama.hiroshima.jp/uploaded/attachment/273294.pdf"
CALENDAR_PDF="/tmp/m099-utsumi-2026-calendar.pdf"
CALENDAR_TXT="/tmp/m099-utsumi-2026-calendar.txt"
CALENDAR_COMPACT="/tmp/m099-utsumi-2026-calendar-compact.txt"
GUIDE_PDF="/tmp/m099-utsumi-guide.pdf"
GUIDE_TXT="/tmp/m099-utsumi-guide.txt"

curl --fail --location --silent --show-error "$CALENDAR_URL" -o "$CALENDAR_PDF"
pdftotext -layout "$CALENDAR_PDF" "$CALENDAR_TXT"

if [[ ! -s "$CALENDAR_TXT" ]]; then
  echo "M099_UTSUMI_2026_CALENDAR_AUDIT_FAILED: extracted text is empty"
  exit 1
fi

# PDF extraction may insert spaces between Japanese glyphs.  Normalize only for
# assertions; retain the unmodified extracted text as the audit artifact.
tr -d '[:space:]' < "$CALENDAR_TXT" > "$CALENDAR_COMPACT"

# Human-provided official 2026 calendar must anchor the current Utsumi scope.
for token in '２０２６年度' '内海町' '燃やせるごみ' '容器包装プラスチックごみ' '資源ごみ' '紙類' '不燃（破砕）ごみ'; do
  if ! grep -Fq "$token" "$CALENDAR_COMPACT"; then
    echo "M099_UTSUMI_2026_CALENDAR_AUDIT_FAILED: missing token: $token"
    exit 1
  fi
done

# The calendar also explicitly points residents to drop-off collection for
# small appliances, rechargeable batteries and waste paper.  Keep this as
# regional/currentness evidence, not as a blanket item-level mapping rule.
for token in '小型家電' '充電式電池' '古紙' '拠点回収'; do
  if ! grep -Fq "$token" "$CALENDAR_COMPACT"; then
    echo "M099_UTSUMI_2026_CALENDAR_AUDIT_FAILED: missing drop-off token: $token"
    exit 1
  fi
done

echo "M099_UTSUMI_2026_CALENDAR_AUDIT: PASS"
echo "M099_UTSUMI_2026_CALENDAR_CONTEXT"
grep -n -E '２０２６年度|内.?海.?町|燃やせるごみ|容器包装プラスチックごみ|資源ごみ|紙類|不燃（破砕）ごみ|小型家電|充電式電池|古紙|拠点回収' "$CALENDAR_TXT" || true

# Supplemental full guide: use only when a common item needs a direct wording,
# preparation rule, special route or exclusion that the calendar cannot prove.
curl --fail --location --silent --show-error "$GUIDE_URL" -o "$GUIDE_PDF"
pdftotext -layout "$GUIDE_PDF" "$GUIDE_TXT"

if [[ ! -s "$GUIDE_TXT" ]]; then
  echo "M099_UTSUMI_GUIDE_AUDIT_FAILED: extracted text is empty"
  exit 1
fi

PATTERN='ペットボトル|キャップ|ラベル|アルミ缶|スチール缶|びん|ビン|トレイ|弁当|菓子|レジ袋|発泡スチロール|新聞|段ボール|ダンボール|雑誌|紙パック|生ごみ|ティッシュ|おむつ|衣類|傘|陶磁器|ガラス|包丁|乾電池|ボタン電池|充電式電池|モバイルバッテリー|蛍光灯|電球|スプレー缶|ライター|小型家電|布団|テレビ|エアコン|冷蔵庫|洗濯機|パソコン|食用油|剪定枝|枝木'

echo "M099_UTSUMI_GUIDE_ITEM_CONTEXT_BEGIN"
grep -n -E -C 2 "$PATTERN" "$GUIDE_TXT" || true
echo "M099_UTSUMI_GUIDE_ITEM_CONTEXT_END"
