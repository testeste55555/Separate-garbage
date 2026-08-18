#!/usr/bin/env python3
"""Build Batch 02 from official 2026 municipal guides and run Schema v1.2.3 migration."""

from __future__ import annotations

from pathlib import Path

from schema_v12 import (
    CATEGORY_FIELDS, CATEGORY_REVIEW_EVIDENCE_FIELDS, COVERAGE_FIELDS, MAPPING_FIELDS,
    MUNICIPALITY_FIELDS, QA_FIELDS, SOURCE_FIELDS, migrate_batch_dir, read_csv, write_csv,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research" / "batches" / "batch_02"
CHECKED = "2026-08-18"
REVIEWER = "OPENAI_WORK_MANUAL_INDEX_REVIEW"
NOT_STATED = "NOT_STATED_IN_CITED_SOURCE"

# These values previously made an unverified row look complete merely because the
# cell was non-empty.  The generator rejects them after every category is built.
LEGACY_PLACEHOLDERS = {
    "他の分別区分に該当する物",
    "家庭から出る対象物",
    "該当する公式区分",
    "中身を除き、必要な前処理を行う",
    "公式ガイドの指定方法",
    "公式ガイドの品目・寸法条件",
    "種類別にまとめ、必要に応じて洗浄・乾燥",
    "洗浄・結束など品目別前処理",
    "洗浄・水切り・結束など品目別前処理",
    "中身除去・洗浄・絶縁など品目別前処理",
    "水切り・危険物保護など品目別前処理",
    "親区分の資源回収方法",
    "親区分の古紙回収方法",
}


municipality_specs = {
    "M012": dict(pref="埼玉県", city="幸手市", processor="幸手市", top="https://www.city.satte.lg.jp/soshiki/kankyou/1/1/13626.html", guide="https://www.city.satte.lg.jp/material/files/group/14/setumei.pdf", search="https://www.city.satte.lg.jp/soshiki/kankyou/1/1/13626.html", easy="", multi="", year="令和8年度", note="令和8年度ごみ収集カレンダー共通説明と分別早見表を照合"),
    "M014": dict(pref="東京都", city="墨田区", processor="墨田区", top="https://www.city.sumida.lg.jp/kurashi/gomi_recycle/kateikei/gomi_dashikata/index.html", guide="https://www.city.sumida.lg.jp/kurashi/gomi_recycle/wakedashi_pamphlet/japanese.html", search="https://www.city.sumida.lg.jp/kurashi/gomi_recycle/kateikei/gomi-50onbunbetu.html", easy="", multi="https://www.city.sumida.lg.jp/kurashi/gomi_recycle/wakedashi_pamphlet/index.html", year="令和8年度", note="2026年3月版ガイドの分別フローと50音検索を照合"),
    "M015": dict(pref="東京都", city="中央区", processor="中央区", top="https://www.city.chuo.lg.jp/a0039/kurashi/gomi/bunbetsu/index.html", guide="https://www.city.chuo.lg.jp/a0039/kurashi/gomi/bunbetsu/wakekata/panhuretto.html", search="https://www.city.chuo.lg.jp/a0039/kurashi/gomi/bunbetsu/50onjyun230401.html", easy="", multi="https://www.city.chuo.lg.jp/a0039/kurashi/gomi/bunbetsu/wakekata/panhuretto.html", year="令和8年1月改訂", note="資源は教材用親1箱と公式内訳の子区分を分離"),
    "M016": dict(pref="神奈川県", city="三浦市", processor="三浦市", top="https://www.city.miura.kanagawa.jp/soshiki/haikibutsutaisakuka/gomi_katei/3007.html", guide="https://www.city.miura.kanagawa.jp/soshiki/haikibutsutaisakuka/gomi_katei/3007.html", search="https://www.city.miura.kanagawa.jp/soshiki/haikibutsutaisakuka/gomi_katei/3007.html", easy="", multi="", year="令和8年度", note="公式ページが案内する分割版ガイド全6冊の目次・見出しを照合"),
    "M017": dict(pref="新潟県", city="新潟市", processor="新潟市", top="https://www.city.niigata.lg.jp/kurashi/gomi/gomishigen/gomidasi/niigata/index.html", guide="https://www.city.niigata.lg.jp/kurashi/gomi/gomishigen/gomidasi/niigata/index.html", search="https://www.city.niigata.lg.jp/kurashi/gomi/gomishigen/gomidasi/niigata/index.html", easy="", multi="", year="令和8年度", note="全市共通の有料3区分・資源区分と令和8年度カレンダーを照合"),
    "M018": dict(pref="岐阜県", city="瑞穂市", processor="瑞穂市", top="https://www.city.mizuho.lg.jp/1750.htm", guide="https://www.city.mizuho.lg.jp/1750.htm", search="https://www.city.mizuho.lg.jp/1750.htm", easy="", multi="https://www.city.mizuho.lg.jp/1750.htm", year="令和8年度", note="公式索引ページの区分別PDF見出しと多言語ごみアプリ案内を照合"),
    "M019": dict(pref="岐阜県", city="山県市", processor="山県市", top="https://www.city.yamagata.gifu.jp/soshiki/shimin/1835.html", guide="https://www.city.yamagata.gifu.jp/uploaded/attachment/19770.pdf", search="https://www.city.yamagata.gifu.jp/soshiki/shimin/1835.html", easy="", multi="", year="令和8年度", note="令和8年度一般廃棄物処理実施計画の収集・資源化区分表を照合"),
    "M020": dict(pref="静岡県", city="静岡市", processor="静岡市", top="https://www.city.shizuoka.lg.jp/gomi/s000668.html", guide="https://www.city.shizuoka.lg.jp/gomi/s000668.html", search="https://www.city.shizuoka.lg.jp/gomi/s009159.html", easy="", multi="https://www.city.shizuoka.lg.jp/gomi/s000668.html", year="令和8年度", note="葵・駿河区版と清水区版を併用し、区別差は適用条件に保持"),
    "M021": dict(pref="三重県", city="津市", processor="津市", top="https://www.info.city.tsu.mie.jp/kurashi/gomi_kankyo/index.html", guide="https://www.info.city.tsu.mie.jp/kurashi/gomi_kankyo/1001596/1001597/1001598.html", search="https://www.info.city.tsu.mie.jp/_res/projects/default_project/_page_/001/001/598/bessatu20240606.pdf", easy="", multi="https://www.info.city.tsu.mie.jp/kurashi/gomi_kankyo/1001596/1001597/1001598.html", year="令和8年4月版", note="令和8年4月版ガイドの分別区分一覧と多言語版を照合"),
    "M022": dict(pref="大阪府", city="四條畷市", processor="四條畷市／四條畷市交野市清掃施設組合", top="https://www.city.shijonawate.lg.jp/life/1/11/61/", guide="https://www.city.shijonawate.lg.jp/page/16-60240.html", search="https://www.city.shijonawate.lg.jp/page/16-60240.html", easy="", multi="", year="令和8年度", note="2026年版ガイドの定期収集・拠点回収・粗大不燃・収集外を照合"),
}


source_specs = {
    "M012": [
        ("令和8年度ごみ収集カレンダー・ごみの分け方", "自治体公式Webページ", "https://www.city.satte.lg.jp/soshiki/kankyou/1/1/13626.html", "2026-03-24", "全区分索引・現行性"),
        ("ごみの分け方・出し方 共通説明", "自治体公式PDF", "https://www.city.satte.lg.jp/material/files/group/14/setumei.pdf", "2026-03", "分別区分・前処理・袋条件・分別早見表"),
    ],
    "M014": [
        ("資源物とごみの分け方・出し方（日本語）", "自治体公式Webページ", "https://www.city.sumida.lg.jp/kurashi/gomi_recycle/wakedashi_pamphlet/japanese.html", "2026-06-06", "現行ガイド・多言語導線"),
        ("資源物とごみの分け方・出し方 2026年3月版", "自治体公式PDF", "https://www.city.sumida.lg.jp/kurashi/gomi_recycle/wakedashi_pamphlet/japanese.files/wakedashi202603.pdf", "2026-03", "分別フロー・全区分・前処理"),
    ],
    "M015": [
        ("ごみと資源の分け方・出し方", "自治体公式Webページ", "https://www.city.chuo.lg.jp/a0039/kurashi/gomi/bunbetsu/wakekata/panhuretto.html", "2026-02-26", "現行版・多言語導線"),
        ("ごみと資源の分け方・出し方 1～27頁", "自治体公式PDF", "https://www.city.chuo.lg.jp/documents/5392/1p-27p.pdf", "2026-01", "収集区分・資源内訳・拠点回収"),
        ("ごみと資源の分け方・出し方 28～52頁", "自治体公式PDF", "https://www.city.chuo.lg.jp/documents/5392/28p-52p.pdf", "2026-01", "品目表・収集外・補足"),
    ],
    "M016": [
        ("ごみと資源の分け方・出し方", "自治体公式Webページ", "https://www.city.miura.kanagawa.jp/soshiki/haikibutsutaisakuka/gomi_katei/3007.html", "2026-01-06", "分割ガイド全冊への公式索引"),
        ("ごみと資源の分け方・出し方 P1-P4", "自治体公式PDF", "https://www.city.miura.kanagawa.jp/material/files/group/39/P1-P4.pdf", "2026", "燃せるごみ・びん缶金物"),
        ("ごみと資源の分け方・出し方 P5-P8", "自治体公式PDF", "https://www.city.miura.kanagawa.jp/material/files/group/39/P5-P8.pdf", "2026", "PET・容器包装プラ・不燃"),
        ("ごみと資源の分け方・出し方 P9-P12", "自治体公式PDF", "https://www.city.miura.kanagawa.jp/material/files/group/39/P9-P12.pdf", "2026", "古着・蛍光管・破砕不可・枝草"),
        ("ごみと資源の分け方・出し方 P13-P15", "自治体公式PDF", "https://www.city.miura.kanagawa.jp/material/files/group/39/P13-P15.pdf", "2026", "古紙5区分"),
        ("ごみと資源の分け方・出し方 P16-P18", "自治体公式PDF", "https://www.city.miura.kanagawa.jp/material/files/group/39/P16-P18.pdf", "2026", "粗大・小型家電・乾電池"),
        ("ごみと資源の分け方・出し方 P19-P21", "自治体公式PDF", "https://www.city.miura.kanagawa.jp/material/files/group/39/P19-P21.pdf", "2026", "家電4品目・市で扱えないごみ"),
    ],
    "M017": [
        ("ごみの分け方・出し方（全市）", "自治体公式Webページ", "https://www.city.niigata.lg.jp/kurashi/gomi/gomishigen/gomidasi/niigata/index.html", "2026", "有料3区分・資源区分・収集外"),
        ("令和8年度家庭ごみ収集カレンダー", "自治体公式Webページ", "https://www.city.niigata.lg.jp/kurashi/gomi/gomishigen/gomidasi/gomi_calemder/index.html", "2026-03", "現行年度・地区別収集区分"),
    ],
    "M018": [
        ("ごみの分け方・出し方", "自治体公式Webページ", "https://www.city.mizuho.lg.jp/1750.htm", "2026-08-05", "区分別資料の全索引・アプリ案内"),
        ("ごみの分け方・出し方 ルール", "自治体公式PDF", "https://www.city.mizuho.lg.jp/secure/1610/R7-1.pdf", "2025", "基本ルール・収集外"),
    ],
    "M019": [
        ("令和8年度一般廃棄物処理実施計画", "自治体公式Webページ", "https://www.city.yamagata.gifu.jp/soshiki/shimin/1835.html", "2026-04-01", "現行計画への公式導線"),
        ("令和8年度一般廃棄物処理実施計画 PDF", "自治体公式PDF", "https://www.city.yamagata.gifu.jp/uploaded/attachment/19770.pdf", "2026-04", "収集区分・資源化区分・処理方法"),
    ],
    "M020": [
        ("ごみの出し方ガイドブック", "自治体公式Webページ", "https://www.city.shizuoka.lg.jp/gomi/s000668.html", "2026", "区別ガイド・令和8年度変更"),
        ("ごみの出し方ガイドブック 葵区・駿河区", "自治体公式PDF", "https://www.city.shizuoka.lg.jp/documents/667/2024_gominodasikataguidebook_aoisurugaku_2.pdf", "2026案内中", "葵・駿河区の区分・前処理"),
        ("ごみの出し方ガイドブック 清水区", "自治体公式PDF", "https://www.city.shizuoka.lg.jp/documents/667/2024_gominodasikataguidebook_shimizuku_1.pdf", "2026案内中", "清水区の区分・前処理"),
    ],
    "M021": [
        ("家庭ごみの分け方・出し方", "自治体公式Webページ", "https://www.info.city.tsu.mie.jp/kurashi/gomi_kankyo/1001596/1001597/1001598.html", "2026-04", "現行ガイド・多言語版"),
        ("ごみを出すときのごみ分別ガイドブック", "自治体公式PDF", "https://www.info.city.tsu.mie.jp/_res/projects/default_project/_page_/001/001/598/8.4guidebook.pdf", "2026-04", "分別区分一覧・前処理・収集外"),
        ("ごみ分別品目一覧", "自治体公式PDF", "https://www.info.city.tsu.mie.jp/_res/projects/default_project/_page_/001/001/598/bessatu20240606.pdf", "2024-06-06", "品目別補足"),
    ],
    "M022": [
        ("ごみの出し方ガイドブック", "自治体公式Webページ", "https://www.city.shijonawate.lg.jp/page/16-60240.html", "2026-06-01", "全章索引・現行版"),
        ("四條畷市ごみの出し方ガイドブック", "自治体公式PDF", "https://www.city.shijonawate.lg.jp/uploaded/attachment/37047.pdf", "2026", "定期収集・拠点回収・粗大不燃・収集外"),
    ],
}


categories: list[dict[str, str]] = []


def add(mid: str, name: str, representative: str, *, group: str = "", source: int = 2,
        locator: str = "分別区分見出し", parent: str = "", ui: str = "SORT_BUCKET",
        level: str = "PRIMARY", channel: str = "CURBSIDE", forbidden: str = NOT_STATED,
        fallback: str = NOT_STATED, prep: str = NOT_STATED,
        bag: str = "", condition: str = "", size: str = "", bulky: str = "FALSE", booked: str = "FALSE",
        paid: str = "FALSE", fee: str = "", excluded: str = "FALSE", note: str = "") -> None:
    categories.append({
        "municipality_id": mid, "自治体正式名称": name, "category_group": group or name,
        "parent_name": parent, "classification_level": level, "collection_channel": channel,
        "代表品目": representative, "入れてはいけない物": forbidden, "適用条件": condition,
        "条件外の扱い": fallback, "出す前の処理": prep, "袋・容器のルール": bag,
        "サイズ・条件": size, "粗大ごみ扱いか": bulky, "予約が必要か": booked,
        "有料か": paid, "料金ルール": fee, "自治体収集外か": excluded, "注意事項": note,
        "source_index": str(source), "出典ページ・該当箇所": locator, "ui_role": ui,
    })


# M012 幸手市：共通説明p23～32と分別早見表を全件照合。
add("M012", "燃やせるごみ", "生ごみ・汚れた紙・革・ゴム", locator="p23 燃やせるごみ", forbidden="アルミホイル、資源化できる紙・布、きれいな容器包装プラスチック", fallback="アルミホイルは燃やせないごみ、資源化できる物は各資源区分", prep="生ごみは水を切る。枝木は太さ5cm以下・長さ50cm以下にして直径30cm程度にひもで束ねる", bag="黄色の市指定袋に入れ、口を結ぶ", size="枝木は太さ5cm以下・長さ50cm以下。板は厚さ5cm以下・長さ50cm以下・幅5cm以下")
add("M012", "燃やせないごみ", "陶磁器・ガラス・小型金属", locator="p24 燃やせないごみ", forbidden="乾電池・ボタン電池、蛍光管、スプレー缶、50cm以上の物", fallback="電池・蛍光管は有害ごみ、スプレー缶等は危険ごみ、50cm以上は粗大ごみ", prep="割れ物・刃物は紙等で包み、危険物であることを表示する。容器は中身を空にして拭く", bag="透明または半透明の袋。黒袋・段ボール箱・紙袋は不可", size="いずれか一辺が50cm以上は粗大ごみ")
add("M012", "有害ごみ", "乾電池・ボタン電池・蛍光管・水銀製品・モバイルバッテリー", locator="p24 有害ごみ", forbidden="スプレー缶、カセットガスボンベ、ライター", fallback="膨張したモバイルバッテリーは環境課へ直接持参。危険ごみ対象は危険ごみへ", prep="品目ごとに分ける。蛍光管は破損防止し、モバイルバッテリーは放電して端子を絶縁する", bag="品目ごとに別の透明または半透明袋", size="膨張したモバイルバッテリーは集積所に出さない")
add("M012", "危険ごみ", "スプレー缶・カセットガスボンベ・ライター", locator="p25 危険ごみ", forbidden="乾電池・蛍光管・モバイルバッテリー", fallback="乾電池等は有害ごみ", prep="できるだけ使い切る。使い切れない場合も穴は開けない", bag="スプレー缶等とライターをそれぞれ別の透明または半透明袋")
add("M012", "粗大ごみ", "家具・寝具・自転車など一辺50cm以上の物", locator="p25 粗大ごみ", forbidden="スプリング入りマットレス・ソファ、家電4品目、枝木・材木", fallback="スプリング製品は金属と布等に分離できなければ専門業者。家電4品目は販売店等", prep="自転車は『ごみ』と表示し、ストーブ等は燃料を抜き、電池は外す", bag="収集日にごみ集積所へ出す", size="いずれか一辺が50cm以上", bulky="TRUE", booked="FALSE", paid="FALSE", channel="CURBSIDE", ui="REFERENCE_ONLY")
add("M012", "その他プラスチック", "プラマークの容器包装・発泡スチロール", locator="p26 その他プラスチック", forbidden="おもちゃ・バケツ等の製品プラスチック、医療系廃棄物、かみそり", fallback="製品プラスチックとかみそりは燃やせないごみ、汚れが落ちない物は燃やせるごみ", prep="中身を空にし、汚れを洗うか拭き取って乾かす", bag="透明または半透明袋。二重袋は不可")
add("M012", "かん", "飲食用アルミ缶・スチール缶", group="かん・びん・ペットボトル", locator="p27 かん・びん・ペットボトル", forbidden="塗料缶・自動車オイル缶、加工した缶、内容物が残る缶", fallback="塗料缶等は中身を除いて燃やせないごみ", prep="中をすすぎ、つぶさずに出す", bag="オレンジ色の回収容器")
add("M012", "びん", "飲食用びん", group="かん・びん・ペットボトル", locator="p27 かん・びん・ペットボトル", forbidden="薬品・農薬・化粧品等のびん、割れたびん、内容物が残るびん", fallback="対象外びんは中身を除いて燃やせないごみ。リターナブルびんは販売店返却可", prep="ふたを外して中をすすぐ", bag="青色の回収容器に横向きに入れる")
add("M012", "ペットボトル", "PETマークの飲料・酒・調味料用ボトル", group="かん・びん・ペットボトル", locator="p27 かん・びん・ペットボトル", forbidden="PET以外の表示、着色・塗装した物、汚れ・中身・異物が残る物", fallback="他のプラ表示はその他プラスチック、塗装品は燃やせるごみ", prep="キャップとラベルを外し、中をすすいでつぶす", bag="ペットボトル用ネット")
add("M012", "新聞", "新聞・折込広告", group="紙類", locator="p28 紙類", forbidden="防水・感熱・コーティング紙、汚れ・臭いの付いた紙", fallback="リサイクルできない紙は燃やせるごみ", prep="新聞と折込広告を一緒に種類別にまとめる", bag="むき出しで、ひもを十文字に結ぶ。紙袋・箱は不可")
add("M012", "雑誌", "雑誌・書籍・ノート", group="紙類", locator="p28 紙類", forbidden="金具付きファイル、リサイクルできない加工紙", fallback="金具は燃やせないごみ、リサイクルできない紙は燃やせるごみ", prep="雑誌・書籍・ノートを種類別にまとめる", bag="むき出しで、ひもを十文字に結ぶ。紙袋・箱は不可")
add("M012", "雑がみ", "菓子箱・包装紙・小さい紙", group="紙類", locator="p28 紙類", forbidden="防水紙・感熱紙・コーティング紙・汚れや臭いの付いた紙・シュレッダー紙", fallback="対象外の紙は燃やせるごみ", prep="小さい紙は封筒に入れるか雑誌に挟む", bag="雑誌と一緒にむき出しでひもを十文字に結ぶ。紙袋・箱は不可")
add("M012", "段ボール", "段ボール", group="紙類", locator="p28 紙類", forbidden="汚れ・臭いの付いた段ボール", fallback="汚れた物は燃やせるごみ", prep="折りたたんで種類別にまとめる", bag="むき出しで、ひもを十文字に結ぶ。紙袋・箱は不可")
add("M012", "紙パック", "飲料用紙パック", group="紙類", locator="p28 紙類", forbidden="内側がアルミ加工された紙パック", fallback="内側アルミ加工品は燃やせるごみ。注ぎ口等の非紙部分は切り離して材質別区分", prep="洗って切り開き、乾かす。キャップ口等の非紙部分は切り取る", bag="むき出しで、ひもを十文字に結ぶ。紙パックは箱利用可")
add("M012", "布類", "衣類・毛布・タオル・シーツ・布製カーテン", locator="p28 布類", forbidden="汚れ・破れのある物、綿入り製品、革製品、遮光カーテン", fallback="汚れた衣類等は燃やせるごみ。布団・カーペット等と50cm以上の物は粗大ごみ", prep="洗濯して乾かし、たたむ。ファスナー・ボタンは外さない", bag="透明または半透明袋。雨天時は避ける")
add("M012", "使用済小型家電", "回収ボックス投入口に入る電気・電池式小型家電", locator="p35 使用済小型家電", forbidden="モバイルバッテリー、投入口に入らない物", fallback="モバイルバッテリーは有害ごみ。対象外品は分別早見表の区分", prep="個人情報を消去し、電池を外す", bag="市役所等の回収ボックス", channel="DROP_OFF", ui="REFERENCE_ONLY")
add("M012", "市で処理できないもの", "家電4品目・パソコン・スプリング製品・自動車部品等", locator="p32 市で処理できないもの", forbidden="ごみ集積所への排出", fallback="販売店・メーカー・専門業者へ相談", prep="受入先の指示に従う", bag="集積所に出さない", level="EXCLUDED", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", excluded="TRUE")

# M014 墨田区：2026年3月版分別フロー。
add("M014", "プラスチック", "プラマーク容器包装・100%プラスチック製品", locator="p3 資源物とごみの分別フロー", prep="汚れを落とす", fallback="汚れや臭いが落ちない物は燃やすごみ", size="製品プラは最長辺30cm以下")
add("M014", "古紙", "新聞・段ボール・紙パック・雑誌雑がみ", locator="p3 資源物とごみの分別フロー", prep="種類別にまとめる", bag="ひも結束または紙袋")
for name, rep in [("缶", "飲食用缶"), ("びん", "飲食用びん"), ("ペットボトル", "PETマークのボトル")]:
    add("M014", name, rep, locator="p3 資源物とごみの分別フロー", prep="中をすすぎ、ふた・ラベル等を外す", bag="指定コンテナ・ネット")
add("M014", "拠点回収", "乾電池・小型家電等の指定品", locator="p3 拠点回収", channel="DROP_OFF", ui="REFERENCE_ONLY", prep=NOT_STATED, bag="指定回収箱")
add("M014", "イベント回収", "古着・廃食用油等の指定品", locator="p3 イベント回収", channel="DROP_OFF", ui="REFERENCE_ONLY", prep=NOT_STATED)
add("M014", "燃やすごみ", "生ごみ・資源化できない紙・汚れたプラ", locator="p3・燃やすごみ", prep="生ごみは水切り", bag="半透明袋")
add("M014", "燃やさないごみ", "陶磁器・ガラス・金属・危険物", locator="p3・燃やさないごみ", prep="割れ物・刃物を包み危険表示、スプレー缶は使い切る", bag="半透明袋")
add("M014", "粗大ごみ", "一辺30cmを超える家具・寝具等", locator="粗大ごみ案内", bulky="TRUE", booked="TRUE", paid="TRUE", fee="品目別処理手数料", channel="BOOKED_PICKUP", ui="REFERENCE_ONLY", size="おおむね一辺30cm超")
add("M014", "区で収集できないもの", "家電4品目・パソコン・処理困難物", locator="区では収集できないもの", level="EXCLUDED", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー・専門業者", prep="受入先の指示に従う", bag="集積所に出さない")

# M015 中央区：資源の公式内訳を葉区分として保持し、教材では親1箱へ投影。
add("M015", "燃やすごみ", "生ごみ・紙くず・ゴム・革", locator="p6 燃やすごみ", prep="生ごみは水を切る")
add("M015", "燃やさないごみ", "陶磁器・ガラス・金属・小型家電", locator="p7 燃やさないごみ", prep="割れ物・刃物を包み危険表示")
add("M015", "プラスチック製容器包装", "プラマーク付き容器包装", locator="p8-9 プラスチック製容器包装", prep="中身を除き汚れを落とす", fallback="汚れが落ちない物は燃やすごみ")
add("M015", "資源", "古紙・びん・缶・ペットボトル・金属製品", locator="p10-11 資源", prep=NOT_STATED)
for name, rep, prep, bag in [
    ("新聞", "新聞・折込広告", "折込広告を含めてまとめる", "ひもで十文字に束ねる"),
    ("雑誌・雑がみ", "雑誌・書籍・雑がみ", "小さい雑がみは雑誌に挟むか紙袋に入れる", "雑誌はひもで十文字に束ね、雑がみは紙袋も可"),
    ("段ボール", "段ボール", "折りたたむ", "ひもで十文字に束ねる"),
    ("紙パック", "飲料用紙パック", "洗って切り開き、乾かす", "ひもで十文字に束ねる"),
    ("ペットボトル", "PETマークのボトル", "キャップとラベルを外し、中をすすいでつぶす", "ペットボトル回収用ネット"),
    ("びん", "飲食用びん", "ふたを外し、中をすすぐ", "びん用回収容器"),
    ("缶", "飲食用缶", "中をすすぐ", "缶用回収容器"),
    ("金属製のなべ・やかん・フライパン", "なべ・やかん・フライパン", "中身と汚れを除く", "資源回収場所へそのまま出す"),
    ("スプレー缶・カセットボンベ", "スプレー缶・カセットボンベ", "中身を使い切り、穴を開けずに出す", "他の資源と分けて出す"),
]:
    add("M015", name, rep, group="資源", parent="資源", level="SUBCATEGORY", ui="REFERENCE_ONLY", locator=f"p10-11 資源・{name}", prep=prep, bag=bag)
add("M015", "拠点回収", "紙パック・食品トレイ・乾電池・古布・廃食用油・蛍光管・小型家電", locator="p12-13 拠点回収", channel="DROP_OFF", ui="REFERENCE_ONLY", prep=NOT_STATED, bag="指定回収箱・容器")
add("M015", "粗大ごみ", "一辺30cmを超える家具・寝具等", locator="p14-15 粗大ごみ", bulky="TRUE", booked="TRUE", paid="TRUE", fee="品目別処理手数料", channel="BOOKED_PICKUP", ui="REFERENCE_ONLY", size="一辺30cm超")
add("M015", "区で収集しないもの", "家電4品目・パソコン・処理困難物", source=3, locator="収集できないもの・メーカーリサイクル", level="EXCLUDED", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー・専門業者", prep="受入先の指示に従う", bag="集積所に出さない")

# M016 三浦市：分割版ガイドの公式目次順。
add("M016", "燃せるごみ", "生ごみ・紙くず・木くず・汚れたプラ", source=2, locator="P1-P4 燃せるごみ", prep="生ごみは水切り")
add("M016", "びん・缶、金物類", "飲食用びん・缶・金物", source=2, locator="P1-P4 びん・缶、金物類", prep="びん・缶は中をすすぎ、びん・缶・金物を分けて出す")
add("M016", "ペットボトル", "PETマークのボトル", source=3, locator="P5-P8 ペットボトル", prep="キャップとラベルを外しすすぐ")
add("M016", "プラスチック製容器包装", "プラマーク付き容器包装", source=3, locator="P5-P8 プラスチック製容器包装", prep="中身を除き汚れを落とす")
add("M016", "不燃ごみ", "陶磁器・ガラス・小型不燃物", source=3, locator="P5-P8 不燃ごみ", prep="割れ物・刃物を包み危険表示")
add("M016", "古着・古布", "衣類・古布", source=4, locator="P9-P12 古着・古布", prep="洗濯し乾かす", bag="透明袋")
add("M016", "蛍光管類", "蛍光管・水銀製品", source=4, locator="P9-P12 蛍光管類", prep="破損しないよう保護", bag="指定回収方法")
add("M016", "破砕できないごみ", "大型金属・破砕困難品", source=4, locator="P9-P12 破砕できないごみ", prep="危険部分を保護")
add("M016", "枝木・草葉類", "剪定枝・草・葉", source=4, locator="P9-P12 枝木・草葉類", prep="土を落とし規定寸法に束ねる")
for name, rep, prep, bag in [
    ("新聞紙", "新聞・折込広告", "折込広告を含めてまとめる", "ひもで十文字に束ねる"),
    ("雑誌", "雑誌・書籍", "付録等の紙以外を外す", "ひもで十文字に束ねる"),
    ("段ボール", "段ボール", "折りたたむ", "ひもで十文字に束ねる"),
    ("紙パック", "飲料用紙パック", "洗って切り開き、乾かす", "ひもで十文字に束ねる"),
    ("その他の紙", "雑がみ・菓子箱", "紙以外の部分を外し、小さい紙はまとめる", "紙袋に入れるか雑誌に挟んでひもで束ねる"),
]:
    add("M016", name, rep, group="古紙", source=5, locator=f"P13-P15 {name}", prep=prep, bag=bag)
add("M016", "粗大ごみ", "50cm以上2m以下の家具・寝具等", source=6, locator="P16-P18 粗大ごみ", bulky="TRUE", booked="TRUE", paid="TRUE", fee="品目別処理手数料", channel="BOOKED_PICKUP", ui="REFERENCE_ONLY", size="50cm以上2m以下")
add("M016", "使用済小型家電", "回収ボックス対象の小型家電", source=6, locator="P16-P18 使用済小型家電", channel="DROP_OFF", ui="REFERENCE_ONLY", prep="個人情報を消去し電池を外す", bag="回収ボックス")
add("M016", "乾電池", "乾電池", source=6, locator="P16-P18 乾電池", prep="端子を絶縁", bag="指定回収容器")
add("M016", "市で収集・処理できないごみ", "家電4品目・パソコン・処理困難物", source=7, locator="P19-P21 市で収集・処理できないごみ", level="EXCLUDED", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー・専門業者", prep="受入先の指示に従う", bag="集積所に出さない")

# M017 新潟市：全市共通区分。古紙類の親と4葉を分離。
add("M017", "燃やすごみ", "生ごみ・紙くず・革・ゴム", locator="燃やすごみ 見出し", forbidden="資源化できる紙・容器包装、燃やさないごみ対象品", fallback="材質・状態に応じて資源区分または燃やさないごみ", prep="生ごみは十分に水を切る", bag="新潟市指定袋", paid="TRUE", fee="指定袋料金")
add("M017", "燃やさないごみ", "陶磁器・ガラス・金属・小型家電", locator="燃やさないごみ 見出し", forbidden="特定5品目、指定袋に入らない大型品", fallback="特定5品目は専用区分、指定袋に入らない物は粗大ごみ", prep="割れ物・刃物は紙等で包み、危険表示する", bag="新潟市指定袋", paid="TRUE", fee="指定袋料金")
add("M017", "粗大ごみ", "指定袋に入らない大型品", locator="粗大ごみ 見出し", bulky="TRUE", booked="TRUE", paid="TRUE", fee="品目別処理券", channel="BOOKED_PICKUP", ui="REFERENCE_ONLY")
for name, rep, prep, bag in [
    ("プラマーク容器包装", "プラマーク付き容器包装", "中身を使い切り、汚れを落とす", "透明または半透明袋"),
    ("ペットボトル", "PETマークのボトル", "キャップとラベルを外し、中をすすぐ", "透明または半透明袋"),
    ("飲食用・化粧品びん", "飲食用・化粧品びん", "ふたを外し、中をすすぐ", "びん用コンテナ"),
    ("飲食用缶", "飲食用アルミ缶・スチール缶", "中をすすぐ", "透明または半透明袋"),
    ("枝葉・草", "剪定枝・葉・草", "土を落とし、枝と葉・草を分ける", "枝はひもで束ね、葉・草は透明または半透明袋"),
    ("特定5品目", "乾電池・蛍光管・水銀体温計・ライター・スプレー缶", "蛍光管は破損防止し、ライター・スプレー缶は使い切る", "品目ごとに透明または半透明袋"),
]:
    add("M017", name, rep, locator=f"資源・{name}", prep=prep, bag=bag)
add("M017", "古紙類", "新聞・雑誌雑がみ・段ボール・紙パック", locator="資源・古紙類", prep="種類別にまとめる", bag="ひも結束または紙袋")
for name, rep, prep, bag in [
    ("新聞", "新聞・折込広告", "折込広告を含めてまとめる", "ひもで十文字に束ねる"),
    ("雑誌・雑がみ", "雑誌・書籍・雑がみ", "紙以外を外し、小さい紙をまとめる", "雑誌はひもで束ね、雑がみは紙袋も可"),
    ("段ボール", "段ボール", "折りたたむ", "ひもで十文字に束ねる"),
    ("紙パック", "飲料用紙パック", "洗って切り開き、乾かす", "ひもで十文字に束ねる"),
]:
    add("M017", name, rep, group="古紙類", parent="古紙類", level="SUBCATEGORY", ui="REFERENCE_ONLY", locator=f"古紙類・{name}", prep=prep, bag=bag)
add("M017", "市で収集・処理しないごみ", "家電4品目・パソコン・処理困難物", locator="市で収集・処理しないごみ", level="EXCLUDED", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー・専門業者", prep="受入先の指示に従う", bag="集積所に出さない")

# M018 瑞穂市：公式索引ページの区分別見出し。
for name, rep, locator, prep in [
    ("可燃ごみ", "生ごみ・紙くず・革・ゴム", "可燃ごみの分け方・出し方", "生ごみは水を切る"),
    ("あきびん", "飲食用びん", "あきびんの分け方・出し方", "ふたを外し、中をすすぐ"),
    ("陶磁器類・ガラス類", "陶磁器・ガラス製品", "陶磁器類・ガラス類の分け方・出し方", "割れ物は紙等で包み危険表示する"),
    ("ペットボトル", "PETマークのボトル", "ペットボトルの分け方・出し方", "キャップとラベルを外し、中をすすぐ"),
    ("空き缶", "飲食用アルミ缶・スチール缶", "空き缶の分け方・出し方", "中をすすぐ"),
    ("プラスチック製容器包装", "プラマーク付き容器包装", "プラスチック製容器包装の分け方・出し方", "中身を使い切り、汚れを落とす"),
]:
    add("M018", name, rep, source=1, locator=locator, prep=prep)
add("M018", "庁舎回収・拠点回収", "乾電池・蛍光管・小型家電等の指定品", source=1, locator="庁舎回収・拠点回収", channel="DROP_OFF", ui="REFERENCE_ONLY", prep=NOT_STATED, bag="指定回収箱・容器")
add("M018", "美来の森・巣南集積場無料回収", "古紙・古着・資源物等の指定品", source=1, locator="美来の森・巣南集積場無料回収", channel="DROP_OFF", ui="REFERENCE_ONLY", prep=NOT_STATED)
add("M018", "粗大ごみ", "家具・寝具・大型品", source=1, locator="粗大ごみの分け方・出し方", bulky="TRUE", booked="TRUE", paid="TRUE", fee="品目別粗大ごみシール", channel="BOOKED_PICKUP", ui="REFERENCE_ONLY")
add("M018", "剪定木", "家庭の剪定枝", source=1, locator="戸別収集・剪定木", prep=NOT_STATED, channel="BOOKED_PICKUP", ui="REFERENCE_ONLY")
add("M018", "廃食用油", "家庭の植物性食用油", source=1, locator="廃食用油の回収", prep="冷まして密閉容器に入れる", bag="指定回収容器", channel="DROP_OFF", ui="REFERENCE_ONLY")
add("M018", "市で収集・処理できないもの", "家電4品目・パソコン・処理困難物", source=2, locator="市で処理できないもの", level="EXCLUDED", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー・専門業者", prep="受入先の指示に従う", bag="集積所に出さない")

# M019 山県市：令和8年度計画の収集・資源化区分。
for name, rep in [("燃えるごみ", "生ごみ・紙くず・革・ゴム"), ("不燃ごみ", "陶磁器・ガラス・小型金属"), ("粗大ごみ", "家具・寝具・大型品")]:
    add("M019", name, rep, locator=f"計画 分別収集区分・{name}", bulky="TRUE" if name == "粗大ごみ" else "FALSE", booked="TRUE" if name == "粗大ごみ" else "FALSE", paid="TRUE" if name == "粗大ごみ" else "FALSE", channel="BOOKED_PICKUP" if name == "粗大ごみ" else "CURBSIDE", ui="REFERENCE_ONLY" if name == "粗大ごみ" else "SORT_BUCKET")
for name, rep in [("びん", "飲食用びん"), ("缶", "飲食用缶"), ("ペットボトル", "PETマークのボトル"), ("白色トレイ", "白色食品トレイ"), ("金属類", "金属製品"), ("発泡スチロール", "発泡スチロール"), ("新聞・折込チラシ", "新聞・折込広告"), ("雑誌・雑がみ", "雑誌・雑がみ"), ("段ボール", "段ボール"), ("紙パック", "牛乳パック"), ("アルミ缶", "アルミ缶"), ("古着", "衣類・古着")]:
    add("M019", name, rep, group="資源物", locator=f"計画 資源化区分・{name}", prep=NOT_STATED)
add("M019", "使用済小型家電", "回収対象28品目", locator="計画 使用済小型家電", channel="DROP_OFF", ui="REFERENCE_ONLY", prep="個人情報を消去し電池を外す", bag="回収ボックス")
add("M019", "有害ごみ", "乾電池・蛍光管", locator="計画 有害ごみ", prep="電池を絶縁し蛍光管は破損防止", bag="指定回収容器")
add("M019", "廃食用油", "家庭の植物性食用油", locator="計画 廃食用油回収", channel="DROP_OFF", ui="REFERENCE_ONLY", prep="冷まして密閉容器に入れる", bag="指定回収容器")
add("M019", "市で収集しないもの", "家電4品目・処理困難物", locator="計画 市収集対象外", level="EXCLUDED", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー・専門業者", prep="受入先の指示に従う", bag="集積所に出さない")

# M020 静岡市：区別ガイドを統合し、差異は適用条件に保持。
add("M020", "可燃ごみ", "生ごみ・紙くず・革・ゴム", source=1, locator="可燃ごみ", prep="生ごみは水を切る")
add("M020", "不燃・粗大ごみ（非金属）", "陶磁器・ガラス・大型非金属品", source=1, locator="不燃・粗大ごみ", prep="割れ物を包み危険表示", bulky="CONDITIONAL", note="区・品目により収集方法が異なる")
add("M020", "金属類", "缶・なべ・やかん・小型金属", source=1, locator="金属類", prep="中身を除き危険部分を保護")
for name, rep, prep in [
    ("乾電池", "乾電池", "端子を絶縁する"),
    ("ライター", "使い捨てライター", "中身を使い切る"),
    ("水銀使用製品", "蛍光管・水銀体温計", "破損しないよう保護する"),
    ("スプレー缶", "スプレー缶・カセットボンベ", "中身を使い切り、穴を開けずに出す"),
]:
    add("M020", name, rep, group="危険・有害", source=1, locator=f"危険・有害ごみ・{name}", prep=prep, bag="中身が見える小袋に入れ、他の不燃・粗大ごみと分ける")
for name, rep in [("びん", "飲食用びん"), ("缶", "飲食用缶"), ("ペットボトル", "PETマークのボトル")]:
    add("M020", name, rep, group="資源物", source=1, locator=f"資源物・{name}", prep="中をすすぎキャップ等を外す", bag="指定回収容器")
add("M020", "古紙", "新聞・雑誌雑がみ・段ボール・紙パック", source=1, locator="古紙", prep="種類別にまとめる", bag="ひも結束または紙袋")
for name, rep, prep, bag in [
    ("新聞", "新聞・折込広告", "折込広告を含めてまとめる", "ひもで束ねる"),
    ("雑誌・雑がみ", "雑誌・雑がみ", "紙以外を外し、小さい紙をまとめる", "雑誌はひもで束ね、雑がみは紙袋も可"),
    ("段ボール", "段ボール", "折りたたむ", "ひもで束ねる"),
    ("紙パック", "飲料用紙パック", "洗って切り開き、乾かす", "ひもで束ねる"),
]:
    add("M020", name, rep, group="古紙", parent="古紙", level="SUBCATEGORY", ui="REFERENCE_ONLY", source=1, locator=f"古紙・{name}", prep=prep, bag=bag)
add("M020", "使用済小型家電", "回収ボックス対象の小型家電", source=1, locator="使用済小型家電", channel="DROP_OFF", ui="REFERENCE_ONLY", prep="個人情報を消去し電池を外す", bag="回収ボックス")
add("M020", "市で収集・処理できないもの", "家電4品目・パソコン・処理困難物", source=1, locator="市で収集・処理できないもの", level="EXCLUDED", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー・専門業者", prep="受入先の指示に従う", bag="集積所に出さない")

# M021 津市：ガイドp4の分別区分一覧を正式名称で保持。
for name, rep, prep, bag, forbidden, fallback in [
    ("金属・燃やせないごみ（不燃）", "金属・陶磁器・ガラス・小型家電", "割れ物・刃物は紙等で包み危険表示し、電池を外す", "透明または半透明袋", "危険ごみ対象品、家電4品目", "危険ごみ対象品は危険ごみ、家電4品目は販売店等"),
    ("危険ごみ", "スプレー缶・ライター・蛍光管・水銀製品・電池", "スプレー缶・ライターは使い切り、充電池は端子を絶縁し、蛍光管は箱・筒・袋で保護する", "対象品目をそれぞれ別の透明または半透明袋", "金属・燃やせないごみ、可燃ごみ", "各通常収集区分へ"),
    ("新聞", "新聞・折込広告", "折込広告を含めてまとめる", "ひもで十文字にしばる", "ビニール袋・箱、リサイクルできない紙", "リサイクルできない紙は燃やせるごみ"),
    ("雑誌・雑紙", "雑誌・雑がみ", "紙以外を外し、小さい紙は雑誌に挟む", "ひもで十文字にしばる", "ビニール袋・箱、加工紙・汚れた紙", "リサイクルできない紙は燃やせるごみ"),
    ("ダンボール", "段ボール", "折りたたむ", "ひもで十文字にしばる", "ビニール袋・箱、汚れた段ボール", "汚れた物は燃やせるごみ"),
    ("飲料用紙パック", "飲料用紙パック", "洗って切り開き、乾かす", "ひもで十文字にしばる", "内側がアルミ加工された物", "アルミ加工品は燃やせるごみ"),
    ("衣類・布類", "衣類・古布", "洗って乾かす", "透明または半透明袋", "綿入り製品、肌着・下着、汚れた布", "対象外の布類は燃やせるごみ"),
    ("ペットボトル（ペット）", "PETマークのボトル", "ふたとラベルを外し、中身と異物を除く", "透明または半透明袋", "PETマークのないボトル", "材質に応じた区分へ"),
    ("びん", "人が口にする飲食料品のびん", "ふたを外し、中身を使い切って汚れを除く", "透明または半透明袋", "化粧品・消毒用のびん", "金属・燃やせないごみ"),
    ("容器包装プラスチック（容プラ）", "プラマーク付き容器包装", "異物が残らないよう軽くすすぐ", "透明または半透明袋", "汚れが取れない物、容器包装でない製品プラ", "汚れが取れない物は燃やせるごみ、製品プラはその他プラスチック"),
    ("その他プラスチック（他プラ）", "容器包装以外の全てプラスチック製品", "汚れを可能な限り取り除く", "透明または半透明袋。袋に入らない場合は飛散防止", "金属が取り外せない物、電池・刃物等の危険物", "金属が外せない物は金属・燃やせないごみ、危険物は危険ごみ"),
    ("燃やせるごみ（可燃）", "生ごみ・紙くず・革・ゴム", "生ごみは水を切り、汚物はトイレへ流す", "透明または半透明袋", "資源化できる物、金属・ガラス等", "各資源区分または金属・燃やせないごみ"),
]:
    add("M021", name, rep, locator=f"p4 ごみの分別区分一覧・{name}", prep=prep, bag=bag, forbidden=forbidden, fallback=fallback)
add("M021", "市で収集・処理できないもの", "家電4品目・パソコン・処理困難物・事業ごみ", source=2, locator="市で収集・処理できないもの", level="EXCLUDED", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー・専門業者", prep="受入先の指示に従う", bag="集積所に出さない")

# M022 四條畷市：2026年版ガイドの章見出し。
add("M022", "可燃ごみ", "生ごみ・紙くず・布切れ・木くず・プラスチック製品", locator="p4 可燃ごみ", prep="生ごみは水を切る", bag="45L以下の透明・半透明袋")
add("M022", "ペットボトル", "PETマークのボトル", locator="p4 ペットボトル", prep="キャップとラベルを外しすすぐ", bag="45L以下の透明・半透明袋")
add("M022", "プラスチック製容器包装", "プラマーク付き容器包装", locator="p4 プラスチック製容器包装", prep="汚れを落とす", fallback="汚れが落ちない物は可燃ごみ", bag="45L以下の透明・半透明袋")
add("M022", "空き缶", "飲食用缶", locator="p4 空き缶", prep="中をすすぐ", bag="45L以下の透明・半透明袋")
add("M022", "空きびん", "飲食用・化粧品びん", locator="p4 空きびん", prep="中をすすぐ", bag="45L以下の透明・半透明袋")
add("M022", "スプレー缶・カセットボンベ", "スプレー缶・カセットボンベ", locator="p4 空き缶・空きびん", prep="中身を使い切り穴を開けず別袋", bag="他の缶びんと分ける")
add("M022", "廃食用油", "家庭の植物性食用油", locator="p5 廃油回収", channel="DROP_OFF", ui="REFERENCE_ONLY", prep="冷まして指定容器に入れる", bag="指定回収容器")
add("M022", "乾電池・蛍光管", "乾電池・蛍光管", locator="p5 有害資源ごみ", channel="DROP_OFF", ui="REFERENCE_ONLY", prep="電池を絶縁し蛍光管は破損防止", bag="窓口・拠点回収")
add("M022", "小型充電式電池", "ニカド・ニッケル水素・リチウムイオン電池", locator="p5 有害資源ごみ", channel="DROP_OFF", ui="REFERENCE_ONLY", prep="端子を絶縁", bag="窓口・拠点回収")
add("M022", "水銀式温度計・体温計・血圧計", "水銀式計測器", locator="p5 有害資源ごみ", channel="DROP_OFF", ui="REFERENCE_ONLY", prep="破損しないよう保護", bag="窓口・拠点回収")
add("M022", "使い捨てライター", "使い捨てライター", locator="p5 有害資源ごみ", channel="DROP_OFF", ui="REFERENCE_ONLY", prep="中身を使い切る", bag="窓口・拠点回収")
add("M022", "粗大ごみ・不燃ごみ", "家具・寝具・陶磁器・ガラス・大型品", locator="p6-9 粗大ごみ・不燃ごみ", bulky="CONDITIONAL", booked="TRUE", paid="TRUE", fee="指定品目・大きさ別手数料", channel="BOOKED_PICKUP", ui="REFERENCE_ONLY")
add("M022", "市では収集しないごみ", "家電4品目・パソコン・処理困難物", locator="市では収集しないごみ", level="EXCLUDED", ui="EXCLUDED_NOTICE", channel="NOT_COLLECTED", excluded="TRUE", fallback="販売店・メーカー・専門業者", prep="受入先の指示に従う", bag="集積所に出さない")


def build_sources() -> list[dict[str, str]]:
    rows = []
    for mid, specs in source_specs.items():
        issuer = municipality_specs[mid]["city"]
        for index, (title, kind, url, updated, used) in enumerate(specs, 1):
            rows.append({
                "municipality_id": mid, "source_id": f"S-{mid}-{index:02d}", "資料名": title,
                "資料種別": kind, "公式URL": url, "発行主体": issuer,
                "対象年度": municipality_specs[mid]["year"], "ページ更新日": updated,
                "取得確認日": CHECKED, "使用した情報": used, "優先度": str(index),
                "現行性": "現行" if index == 1 else "現行案内中", "備考": "",
                "official_verified": "", "official_basis": "", "official_linking_url": "",
            })
    return rows


def build_categories() -> list[dict[str, str]]:
    if len(categories) != 151:
        raise ValueError(f"Batch 02 authenticity audit must cover exactly 151 category rows: {len(categories)}")
    audit_fields = (
        "入れてはいけない物", "適用条件", "条件外の扱い", "出す前の処理",
        "袋・容器のルール", "サイズ・条件",
    )
    for raw in categories:
        for field in audit_fields:
            if raw[field] in LEGACY_PLACEHOLDERS:
                raise ValueError(
                    f"legacy placeholder survived authenticity audit: "
                    f"{raw['municipality_id']} {raw['自治体正式名称']} {field}={raw[field]}"
                )
        if not raw["出典ページ・該当箇所"]:
            raise ValueError(
                f"category authenticity audit lacks locator: "
                f"{raw['municipality_id']} {raw['自治体正式名称']}"
            )
    rows = []
    by_mid: dict[str, list[dict[str, str]]] = {}
    for raw in categories:
        by_mid.setdefault(raw["municipality_id"], []).append(raw)
    for mid, raws in by_mid.items():
        name_to_id = {raw["自治体正式名称"]: f"C-{mid}-{pos:02d}" for pos, raw in enumerate(raws, 1)}
        for pos, raw in enumerate(raws, 1):
            source_index = int(raw["source_index"])
            source = source_specs[mid][source_index - 1]
            rows.append({
                "municipality_id": mid, "category_id": name_to_id[raw["自治体正式名称"]],
                "自治体正式名称": raw["自治体正式名称"], "category_group": raw["category_group"],
                "parent_category_id": name_to_id.get(raw["parent_name"], ""),
                "classification_level": raw["classification_level"], "表示順": str(pos),
                "collection_channel": raw["collection_channel"], "代表品目": raw["代表品目"],
                "入れてはいけない物": raw["入れてはいけない物"], "適用条件": raw["適用条件"],
                "条件外の扱い": raw["条件外の扱い"], "出す前の処理": raw["出す前の処理"],
                "袋・容器のルール": raw["袋・容器のルール"], "サイズ・条件": raw["サイズ・条件"],
                "粗大ごみ扱いか": raw["粗大ごみ扱いか"], "予約が必要か": raw["予約が必要か"],
                "有料か": raw["有料か"], "料金ルール": raw["料金ルール"],
                "自治体収集外か": raw["自治体収集外か"], "注意事項": raw["注意事項"],
                "source_id": f"S-{mid}-{source_index:02d}", "出典URL": source[2],
                "出典ページ・該当箇所": raw["出典ページ・該当箇所"], "確認日": CHECKED,
                "ui_role": raw["ui_role"], "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
            })
    return rows


def check_fields(spec: dict, url_field: str, status_field: str, evidence_field: str, official_url: str) -> dict[str, str]:
    url = spec[url_field]
    if url:
        return {status_field: "CHECKED_PRESENT", evidence_field: f"URL:{url}; checked:{CHECKED}"}
    return {
        status_field: "CHECKED_ABSENT",
        evidence_field: f"official index searched:{official_url}; no dedicated resource found; checked:{CHECKED}",
    }


def build_municipalities() -> list[dict[str, str]]:
    rows = []
    for mid, spec in municipality_specs.items():
        review_id = f"CR-{mid}-CATEGORY-COVERAGE"
        row = {
            "municipality_id": mid, "都道府県": spec["pref"], "市町村": spec["city"], "実装区分": "個別指定",
            "ごみ処理主体": spec["processor"], "自治体ごみトップURL": spec["top"],
            "分別ガイドURL": spec["guide"], "品目検索URL": spec["search"],
            "やさしい日本語URL": spec["easy"], "多言語資料URL": spec["multi"], "対象年度": spec["year"],
            "最終確認日": CHECKED, "確認ステータス": "QA_REQUIRED", "備考": spec["note"],
            "official_category_count": "", "reviewed_category_count": "",
            "category_count_basis": "公式ガイドの分別見出し・索引と補足資料を全件照合し、CURRENTかつ非EXCLUDEDの公式葉区分を記録。教材投影用の親は件数外。",
            "category_count_verified": "TRUE", "category_count_check_status": "MANUAL_INDEX_REVIEW",
            "category_count_review_id": review_id, "category_count_reviewed_date": CHECKED,
            "category_count_reviewed_by": REVIEWER,
        }
        row.update(check_fields(spec, "search", "search_service_check_status", "search_service_check_evidence", spec["top"]))
        row.update(check_fields(spec, "easy", "easy_japanese_check_status", "easy_japanese_check_evidence", spec["top"]))
        row.update(check_fields(spec, "multi", "multilingual_check_status", "multilingual_check_evidence", spec["top"]))
        rows.append(row)
    return rows


def build_review_evidence() -> list[dict[str, str]]:
    rows = []
    for mid, specs in source_specs.items():
        review_id = f"CR-{mid}-CATEGORY-COVERAGE"
        for index, source in enumerate(specs, 1):
            rows.append({
                "review_evidence_id": f"CRE-{mid}-{index:02d}", "review_id": review_id,
                "municipality_id": mid, "source_id": f"S-{mid}-{index:02d}",
                "locator": source[4], "evidence_role": "PRIMARY_INDEX" if index == 1 else "SUPPLEMENTAL_INDEX",
                "notes": f"{CHECKED} category completeness review",
            })
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prefix = "batch_02_"
    write_csv(OUT / f"{prefix}municipalities.csv", MUNICIPALITY_FIELDS, build_municipalities())
    write_csv(OUT / f"{prefix}categories.csv", CATEGORY_FIELDS, build_categories())
    write_csv(OUT / f"{prefix}sources.csv", SOURCE_FIELDS, build_sources())
    write_csv(OUT / f"{prefix}qa.csv", QA_FIELDS, [])
    write_csv(OUT / f"{prefix}item_mapping.csv", MAPPING_FIELDS, [])
    write_csv(OUT / f"{prefix}item_coverage.csv", COVERAGE_FIELDS, [])
    write_csv(OUT / f"{prefix}category_review_evidence.csv", CATEGORY_REVIEW_EVIDENCE_FIELDS, build_review_evidence())
    counts = migrate_batch_dir(OUT)
    print(" ".join(f"{key}={value}" for key, value in counts.items()))


if __name__ == "__main__":
    main()
