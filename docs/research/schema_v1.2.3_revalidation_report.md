# Schema v1.2.3 Revalidation / QA Report

実施日：2026-08-18

## Validation

- Pilot：5自治体、60 category行、25 source、76 mapping枝、200 coverage、5/5 QA_PASSED
- Batch 01：10自治体、145 category行、33 source、169 mapping枝、400 coverage、10/10 QA_PASSED
- canonical：15自治体、205 category行、58 source、245 mapping枝、600 coverage、15/15 QA_PASSED
- category review evidence：canonical 22行
- coverage：230 MAPPED_INITIAL / 370 NOT_RESEARCHED

## Gate

- RED TEAM：23/23 PASS
- NEXT_BATCH_GATE：PASS
- APP_READINESS_GATE：HOLD（APP_READY 0/15、600 pair未投入）

石巻市は令和8年3月策定の公式計画第2編17〜18ページを根拠に5種類19分別へ整合した。あきびん4区分は内部SUBCATEGORY、`びん類` は教材投影用SORT_BUCKETとして分離した。

本作業ではBatch 02を開始していない。
