# Style Research Pilot 最終RED TEAM

実施日: 2026-08-20
判定: **24/24 PASS**

`scripts/red_team_style_research.py` は真正データを受理した後、次の改ざんを一件ずつ加えて全件拒否を確認した。

1. 固定順位書換え
2. 尾道市scopeの市全域化
3. 福山市沼隈scope欠落
4. 孤立category_id
5. REFERENCE_ONLYの通常箱化
6. DEFERRED自治体への架空style
7. 共有指定袋色のPRIMARY化
8. 同category複数PRIMARY
9. 装飾色のPRIMARY化
10. 海田町競合色のPRIMARY化
11. DERIVED近似注記欠落
12. 不正HEX
13. 公式色名への推測HEX付与
14. NOT_CONFIRMEDへの色混入
15. FALLBACKの公式source偽装
16. 観測locator欠落
17. 他自治体source参照
18. 非公式ドメイン
19. source台帳locator欠落
20. Stage Aと統合データの不一致
21. CURRENT/SORT_BUCKET projection欠落
22. DEFERRED自治体projection混入
23. 文字コントラスト不足

真正baselineを含め24試験である。

```text
PASS Style Research RED TEAM 24/24
```

中間RED TEAMのscope・複数色・用途差・装飾・競合・色体系なし・非通常UI区分の論点は、TOP10全体のvalidatorと改ざん試験へ反映済み。
