#!/usr/bin/env python3
"""Evidence-backed completion supplement for Batch 07.

Adds M066/M069/M071/M072 after independent official-source review and
updates M065 to the current official village domain while intentionally
keeping it NOT_REVIEWED until its full resident category index can be read.
"""
from __future__ import annotations


def apply(m):
    # Nine municipalities are now fully reviewable; only Chibu remains HOLD.
    m.PASS_TARGETS.update({"M066", "M069", "M071", "M072"})

    # M065 Chibu: current official village communication still points residents
    # to this official garbage/recycling page, but its full category index could
    # not be retrieved in this research session. Keep NOT_REVIEWED and no cats.
    m.municipality_specs["M065"].update(
        top="https://www.vill.chibu.lg.jp/",
        guide="https://www.vill.chibu.lg.jp/gyosei/life/needs/needs05/40",
        current="https://www.vill.chibu.lg.jp/gyosei/life/needs/needs05/40",
        note="2026年の村公式案内が現行の『ゴミ・リサイクル』公式ページへ誘導していることは確認。全分別区分表の本文を取得できないためNOT_REVIEWEDを維持。",
    )
    m.source_specs["M065"] = [
        ("ゴミ・リサイクル", "自治体公式Webページ", m.municipality_specs["M065"]["guide"], "現行案内中", "2026年の村公式案内から現在も住民向けごみ情報として案内される公式ページ。全区分本文は未取得")
    ]

    # M066 Oki-no-shima: current guide + FY2026 calendar + current ordinance.
    m.municipality_specs["M066"].update(
        guide="https://www.town.okinoshima.shimane.jp/kurashi/gomi-kankyo/katei_gomi/2/5013.html",
        current="https://www.town.okinoshima.shimane.jp/soshiki/kankyo/gyomu/1/1/1/242.html",
        note="2026年更新の住民向けガイド・令和8年度カレンダー・現行条例を照合し、可燃/不燃/缶/びん/PET/古紙/粗大の7住民区分を確認。",
    )
    m.source_specs["M066"] = [
        ("ごみの分け方・出し方について", "自治体公式Webページ", m.municipality_specs["M066"]["guide"], "2026-03-02", "現行ガイドブックへの公式導線と住民向け分別運用"),
        ("令和8年度ごみ分別収集カレンダー", "自治体公式Webページ", m.municipality_specs["M066"]["current"], "2026-03-02", "令和8年度に同分別体系が稼働していること"),
        ("隠岐の島町廃棄物の処理及び清掃に関する条例施行規則", "自治体公式例規", "https://www.town.okinoshima.shimane.jp/section/reiki_int/reiki_honbun/r074RG00000334.html", "現行", "家庭ごみの可燃・不燃・缶・びん・PET・古紙・粗大の区分")
    ]
    for name, rep, extra in [
        ("可燃ごみ", "家庭の可燃ごみ", dict(prep="町指定袋・ガイドの方法で出す")),
        ("不燃ごみ", "家庭の不燃ごみ", dict(prep="町指定袋・ガイドの方法で出す")),
        ("缶類", "飲食用缶等", dict(prep="中身を空にし、町指定方法で出す")),
        ("ビン類", "飲食用びん等", dict(prep="中身を空にし、町指定方法で出す")),
        ("ペットボトル", "PETマークのボトル", dict(prep="キャップ・ラベル等は町指定方法に従う")),
        ("古紙類", "新聞・雑誌・段ボール等", dict(prep="古紙の種類・町指定方法に従ってまとめる")),
        ("可燃性・不燃性粗大ごみ", "大型の可燃・不燃家庭ごみ", dict(ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE")),
    ]:
        m.add("M066", name, rep, source=3 if name != "可燃性・不燃性粗大ごみ" else 3,
              locator=f"現行条例・住民ガイド／{name}", **extra)

    # M069 Tsuyama: current official resident guide explicitly defines six types.
    m.municipality_specs["M069"].update(
        top="https://www.city.tsuyama.lg.jp/",
        guide="https://www.city.tsuyama.lg.jp/common/photo/free/files/15157/202207061635570688633.pdf",
        current="https://www.city.tsuyama.lg.jp/common/photo/free/files/7728/202405151157250785579.pdf",
        note="市公式の外国人市民向け生活ガイドが家庭ごみ6種類を明示。保存版分別案内も公式サイトで現行配布され、同体系と整合。",
    )
    m.source_specs["M069"] = [
        ("外国人市民のための生活ガイドブック（やさしい日本語版）", "自治体公式PDF", m.municipality_specs["M069"]["guide"], "現行配布", "家庭ごみを6種類に分ける住民向け公式説明"),
        ("津山市ごみ分別 保存版", "自治体公式PDF", m.municipality_specs["M069"]["current"], "2024", "現行の分別注意点・粗大/資源/古紙等の住民向け補強証拠"),
    ]
    for name, rep, extra in [
        ("可燃（燃やせる）ごみ", "台所ごみ・紙くず・布くず・木くず等", dict(prep="市の指定方法で出す")),
        ("不燃（燃やせない）ごみ", "ガラス・陶磁器・金属・ゴム革製品等", dict(prep="危険物は安全に保護して出す")),
        ("プラスチック容器包装", "商品を入れていたプラスチック容器・袋・包み", dict(prep="汚れを落として出す")),
        ("缶・びん・ペットボトル", "飲料用びん・缶・PETボトル", dict(prep="水洗い。PETはキャップ・ラベルを外す")),
        ("古紙", "新聞・雑誌・段ボール・牛乳パック・雑がみ", dict(prep="古紙の種類ごとに市指定方法で出す")),
        ("粗大（大きい）ごみ", "家具・自転車・大型家庭ごみ等", dict(ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE")),
    ]:
        m.add("M069", name, rep, locator=f"生活ガイドブック／ごみの分け方／{name}", **extra)

    # M071 Kasaoka: current 2026 index + exact current rename + resource HTML.
    m.municipality_specs["M071"].update(
        top="https://www.city.kasaoka.okayama.jp/life/1/11/46/",
        guide="https://www.city.kasaoka.okayama.jp/soshiki/18/7239.html",
        current="https://www.city.kasaoka.okayama.jp/soshiki/18/74031.html",
        note="2026年4月最新版ごみ大百科と現行分別ページを照合。可燃指定袋の現行名称『もやすしかないごみ』を採用。",
    )
    m.source_specs["M071"] = [
        ("最新版 保存版『笠岡市ごみ大百科』", "自治体公式Webページ", m.municipality_specs["M071"]["guide"], "2026-04-01", "令和8年度の家庭ごみ分別体系への公式索引"),
        ("分別収集", "自治体公式Webページ", "https://www.city.kasaoka.okayama.jp/soshiki/18/1822.html", "現行案内中", "カン・紙・布・びん・PET・白色トレイ・プラその他・ガススプレー缶・金属類の9資源区分"),
        ("指定ごみ袋の表記を『もやすしかないごみ』に変更", "自治体公式Webページ", m.municipality_specs["M071"]["current"], "2026-04-01", "令和8年度の可燃ごみ住民向け名称"),
        ("燃えないごみについて", "自治体公式Webページ", "https://www.city.kasaoka.okayama.jp/soshiki/18/1738.html", "現行案内中", "燃えないごみの現行区分"),
        ("スプレー缶等のガス抜き", "自治体公式Webページ", "https://www.city.kasaoka.okayama.jp/soshiki/18/1746.html", "現行案内中", "ガス・スプレー缶は中身を使い切り穴を開けて分別収集")
    ]
    m.add("M071", "もやすしかないごみ", "資源化できない可燃性家庭ごみ", source=3, locator="2026年4月指定袋名称変更", prep="市指定袋で出す")
    m.add("M071", "燃えないごみ", "資源化できない不燃家庭ごみ", source=4, locator="燃えないごみについて")
    for name, rep, prep in [
        ("カン類", "飲食用缶等", "中身を空にし分別収集へ"),
        ("紙類", "新聞・段ボール・紙パック・雑紙", "紙の種類ごとの市指定方法でまとめる"),
        ("布類", "古布・衣類", "市指定方法で出す"),
        ("びん類", "無色・茶色・緑色・その他色・リターナブルびん", "中身を空にして市指定方法で出す"),
        ("ペットボトル", "PETマークのボトル", "キャップ等を外し水洗い"),
        ("白色トレイ", "表裏が白色の対象食品トレイ", "中を洗う。材質条件を確認"),
        ("プラスチック（その他）", "対象プラスチック容器包装・製品", "市の寸法・材質・洗浄条件に従う"),
        ("ガス・スプレー缶", "スプレー缶・カセットガス缶", "中身を使い切り、必ず穴を開けて出す"),
        ("金属類", "市が資源回収する金属類", "市指定方法で出す"),
    ]:
        m.add("M071", name, rep, source=5 if name == "ガス・スプレー缶" else 2,
              locator=f"分別収集／{name}", prep=prep)
    m.add("M071", "粗大ごみ", "指定の大型家庭ごみ", source=1, locator="ごみ・リサイクル／粗大ごみ有料収集", ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE")

    # M072 Ibara: current R7.12.15 guide + FY2026 calendar.
    m.municipality_specs["M072"].update(
        guide="https://www.city.ibara.okayama.jp/soshiki/13/13158.html",
        current="https://www.city.ibara.okayama.jp/soshiki/13/19195.html",
        note="R7.12.15改訂の現行ガイドと令和8年度カレンダーを照合。燃やす/燃やさない、資源ごみ3、資源の日2、粗大の8葉を採用。",
    )
    m.source_specs["M072"] = [
        ("ごみの正しい分け方・出し方ガイド", "自治体公式Webページ", m.municipality_specs["M072"]["guide"], "2026-01-22", "R7.12.15改訂ガイドの8住民区分への公式索引"),
        ("令和8年度上半期ごみ収集カレンダー", "自治体公式Webページ", m.municipality_specs["M072"]["current"], "2026-03-02", "令和8年度の現行運用確認"),
        ("古紙・古着類・廃食油の出し方", "自治体公式Webページ", "https://www.city.ibara.okayama.jp/soshiki/13/1437.html", "2025-12-15", "資源の日の古紙・古着・廃食油の現行条件"),
        ("プラスチック資源の対象拡大", "自治体公式Webページ", "https://www.city.ibara.okayama.jp/soshiki/13/18463.html", "2025-12-15", "製品プラスチックを含む現行資源ごみ（プラ）の条件")
    ]
    for name, rep, extra in [
        ("燃やすごみ", "生ごみ・可燃性家庭ごみ", dict(prep="市指定方法で出す")),
        ("燃やさないごみ", "不燃性家庭ごみ", dict(prep="危険物は安全に保護して出す")),
        ("資源ごみ（びん・缶）", "飲食用びん・缶・スプレー缶", dict(prep="キャップを外し中身を抜き水洗い。スプレー缶は穴を開けガスを抜き切る")),
        ("資源ごみ（ペット）", "PETマークのボトル", dict(prep="市指定方法で出す")),
        ("資源ごみ（プラ）", "容器包装プラ・対象製品プラスチック", dict(source=4, prep="中身・汚れを除き、現行対象条件に従う")),
        ("資源の日（古紙）", "新聞・段ボール・雑誌・紙パック・その他紙", dict(source=3, prep="種類別に市指定方法で結束・排出")),
        ("資源の日（古着・廃食油）", "古着類・家庭の植物性廃食油", dict(source=3, prep="古着は透明袋、廃食油は指定容器に入れて密栓")),
        ("粗大ごみ", "市指定の大型家庭ごみ", dict(ui="REFERENCE_ONLY", channel="BOOKED_PICKUP", bulky="TRUE")),
    ]:
        source = extra.pop("source", 1)
        m.add("M072", name, rep, source=source, locator=f"現行ガイド／{name}", **extra)
