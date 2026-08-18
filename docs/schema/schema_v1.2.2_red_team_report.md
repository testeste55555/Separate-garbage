# Schema v1.2.2 RED TEAM Report

初回実施日：2026-08-17  
候補生成追加試験：2026-08-18  
自動判定：19/19 PASS

v1.2.1の15観点に次の攻撃を追加した。

| # | 新規攻撃観点 | 結果 |
|---:|---|---|
| 16 | 公式総数が空のMANUAL_INDEX_REVIEWを受理し、reviewed count不一致を拒否 | PASS |
| 17 | item evidenceにcategoryとは別の公式sourceを受理し、coverage locator欠落を拒否 | PASS |
| 18 | 共通40品目でPositive evidenceを受理し、Negative/context evidenceだけの候補生成を拒否 | PASS |
| 19 | 複合語collisionとM001「衣類→衣類乾燥機」偽陽性を拒否し、保存済み初期mappingとの同期を確認 | PASS |

全結果：

```text
RED_TEAM_SUMMARY=19/19
SCHEMA_V12_RED_TEAM_PASSED
```

確認した性質：

- MANUAL_INDEX_REVIEWは公式総数を要求しない。
- 手動照合にはreviewed count、公式source、照合根拠、reviewer、review日が必要。
- reviewed countは構造化対象区分数と一致しなければならない。
- mappingのitem evidenceはcategory sourceと異なってよい。
- item evidenceは同一自治体の公式source、source URLとの一致、locatorを必要とする。
- coverageの品目URL・locator欠落はvalidatorが拒否する。
- 初期候補は自治体正式名称・代表品目だけをPositive evidenceとして使用する。
- 除外品、条件外、前処理、注意事項への語の出現だけでは候補を生成しない。
- 共通40品目のPositive/Negative fixtureと既知複合語collisionを継続検査する。

現在データは構造PASSだがNEXT_BATCH_GATEとAPP_READINESS_GATEはいずれもHOLDである。13自治体の実資料レビューとBatch 02は開始していない。
