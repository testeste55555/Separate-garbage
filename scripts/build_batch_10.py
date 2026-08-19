#!/usr/bin/env python3
"""Build Batch 10 from current resident-facing official sources.

Active municipalities: M095, M096, M097, M100, M101, M103, M104, M105.
M098 尾道市 and M099 福山市 are deferred because multiple CURRENT
resident-facing category systems coexist by region. The present municipality-
level schema cannot safely choose a resident's regional variant.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from schema_v12 import (
    CATEGORY_FIELDS, CATEGORY_REVIEW_EVIDENCE_FIELDS, COVERAGE_FIELDS,
    MAPPING_FIELDS, MASTER, MUNICIPALITY_FIELDS, QA_FIELDS, SOURCE_FIELDS,
    migrate_batch_dir, read_csv, write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "research" / "batches" / "batch_10"
CHECKED = "2026-08-19"
REVIEWER = "OPENAI_CHATGPT_BATCH10_REVIEW"
NS = "NOT_STATED_IN_CITED_SOURCE"
TARGETS = {"M095","M096","M097","M100","M101","M103","M104","M105"}
DEFERRED = {"M098", "M099"}
REGISTRY_FIELDS = ["municipality_id","host","authority_type","authority_name","verification_url","verified_date","notes"]

municipality_specs = {
    "M095": dict(pref="広島県", city="呉市", processor="呉市", top="https://www.city.kure.lg.jp/soshiki/19/gomidasicalender2026.html", guide="https://www.city.kure.lg.jp/soshiki/19/gomidasicalender2026.html", note="令和8年度にプラスチック資源を新設した現行7収集区分を公式カレンダーで全件照合。"),
    "M096": dict(pref="広島県", city="竹原市", processor="竹原市／広島中央環境衛生組合", top="https://www.city.takehara.lg.jp/soshikikarasagasu/chiikizukurika/gyomuannai/1_1/2_1/7243.html", guide="https://www.city.takehara.lg.jp/soshikikarasagasu/chiikizukurika/gyomuannai/1_1/2_1/7243.html", note="現行公式ページが維持する5住民区分を採用。2024-2025年の追記修正も反映。"),
    "M097": dict(pref="広島県", city="三原市", processor="三原市", top="https://www.city.mihara.hiroshima.jp/soshiki/23/112554.html", guide="https://www.city.mihara.hiroshima.jp/soshiki/23/112554.html", note="現行分別ガイドの10分別を保持。発火性・有害ごみ内部4区分を公式葉として維持。"),
    "M100": dict(pref="広島県", city="府中市", processor="府中市", top="https://www.city.fuchu.hiroshima.jp/kurashi/gomi_kankyo/gomi/dashokata2/8755.html", guide="https://www.city.fuchu.hiroshima.jp/kurashi/gomi_kankyo/gomi/dashokata2/8755.html", note="現行の家庭ごみ収集5区分を採用。資源ごみ内部は住民が品目別に分けるが収集区分を人工分割しない。"),
    "M101": dict(pref="広島県", city="三次市", processor="三次市", top="https://www.city.miyoshi.hiroshima.jp/garbage-item/search/garbage_rule.php", guide="https://www.city.miyoshi.hiroshima.jp/garbage-item/search/garbage_rule.php", note="現行ごみ出しルールの定期収集9区分を採用。拠点回収3系統はcategory completeness外。"),
    "M103": dict(pref="広島県", city="大竹市", processor="大竹市", top="https://www.city.otake.hiroshima.jp/kurashi/kankyo/1/1592976944471.html", guide="https://www.city.otake.hiroshima.jp/material/files/group/7/reiwa8nenndogomikarenndaAtiku.pdf", note="令和8年度カレンダーと現行50音ガイドを照合。8ステーション区分＋粗大・有害・電池・せん定枝の12公式葉を保持。"),
    "M104": dict(pref="広島県", city="東広島市", processor="東広島市／広島中央環境衛生組合", top="https://www.city.higashihiroshima.lg.jp/soshiki/seikatsukankyo/8/4/1/index.html", guide="https://www.city.higashihiroshima.lg.jp/material/files/group/18/gomibook_all.pdf", note="現行ごみブック・条例・2026年公式案内を照合。11住民区分を保持。"),
    "M105": dict(pref="広島県", city="廿日市市", processor="廿日市市", top="https://www.city.hatsukaichi.hiroshima.jp/soshiki/31/78499.html", guide="https://www.city.hatsukaichi.hiroshima.jp/soshiki/31/78499.html", note="令和8年4月版早見表の6種10分別を採用。資源ごみ5葉は投影親の下に保持。"),
}

source_specs = {
    "M095": [
        ("ごみ出しカレンダー（令和8年度版）", "自治体公式Webページ", municipality_specs["M095"]["guide"], "2026-06-29", "令和8年度の7収集区分とプラスチック資源新設"),
        ("ごみの分別収集", "自治体公式Webページ", municipality_specs["M095"]["guide"], "2026-06-29", "各区分の代表品目・市で収集しないごみ"),
    ],
    "M096": [
        ("ごみの分類方法と出し方", "自治体公式Webページ", municipality_specs["M096"]["guide"], "2025-04-01", "現行5区分、2024-2025年追記修正、各ページへの公式索引"),
        ("家庭ごみの分別と出し方", "自治体公式PDF", "https://www.city.takehara.lg.jp/material/files/group/7/01gomi.pdf", "現行配布", "もやせる物・リサイクルする物・資源物・粗大ごみ・有害ごみの5区分"),
    ],
    "M097": [
        ("ごみの分別方法が一部，変わりました-2", "自治体公式Webページ", municipality_specs["M097"]["guide"], "現行案内中", "10分別の正式名称と区分変更"),
        ("違反指導ステッカー（黄色）", "自治体公式Webページ", "https://www.city.mihara.hiroshima.jp/soshiki/23/112747.html", "現行案内中", "10分別の住民向けチェック項目"),
    ],
    "M100": [
        ("家庭ごみ処理有料化指定袋（令和6年4月～）", "自治体公式Webページ", municipality_specs["M100"]["guide"], "2026-05-29", "可燃・容器包装プラ・資源・PET・埋立の現行収集体系"),
        ("（仮称）府中市クリーンセンター施設整備基本計画", "自治体公式PDF", "https://www.city.fuchu.hiroshima.jp/material/files/group/16/kihonkeikaku.pdf", "現行計画", "家庭ごみ収集5区分の公式総数と構成"),
        ("広報ふちゅう 2026年1月号", "自治体公式PDF", "https://www.city.fuchu.hiroshima.jp/material/files/group/2/132810.pdf", "2026-01", "資源ごみ内の小型家電・電池・びん缶とスプレー缶現行前処理"),
    ],
    "M101": [
        ("ごみ出しのルール", "自治体公式Webページ", municipality_specs["M101"]["guide"], "現行案内中", "毎週3・資源日2・ごみ日4の9定期収集区分"),
        ("ごみの分け方検索", "自治体公式Webページ", "https://www.city.miyoshi.hiroshima.jp/garbage-item/search/search.php", "現行案内中", "9区分と拠点回収3系統を区別する現行索引"),
    ],
    "M103": [
        ("令和8年度大竹市ごみ収集カレンダー", "自治体公式PDF", municipality_specs["M103"]["guide"], "令和8年度", "8ステーション区分、粗大、有害、電池類、せん定枝"),
        ("家庭ごみの分別ガイド", "自治体公式Webページ", municipality_specs["M103"]["top"], "現行案内中", "各区分の代表品目・分岐・有害ごみ等"),
        ("大竹市一般廃棄物処理基本計画", "自治体公式PDF", "https://www.city.otake.hiroshima.jp/material/files/group/7/ippanhaikibutushorikihonkeikaku.pdf", "2026", "①〜⑫の分別・処理フローの補強証拠"),
    ],
    "M104": [
        ("家庭から出るごみの分別・出し方について", "自治体公式Webページ", municipality_specs["M104"]["top"], "現行案内中", "現行ごみブック・品目別公式ページへの索引"),
        ("ごみを直接ごみ処理施設へ搬入するときは", "自治体公式Webページ", "https://www.city.higashihiroshima.lg.jp/soshiki/seikatsukankyo/8/4/1/21963.html", "2026-07", "11分別種と搬入施設"),
        ("東広島市廃棄物の処理、清掃等に関する条例施行規則", "自治体公式例規", "https://www.city.higashihiroshima.lg.jp/section/reiki_int/reiki_honbun/m313RG00000594.html", "現行", "燃やせる・瓶缶・リサイクルプラ・PET・その他プラ・危険・粗大・有害・古紙体系"),
    ],
    "M105": [
        ("家庭ごみの正しい分け方の早見表（令和8年4月版）", "自治体公式Webページ", municipality_specs["M105"]["guide"], "2026-05-18", "燃やせる・資源・埋立・大型・小型複雑・有害と資源5細分"),
        ("ごみ分別一覧表（令和8年4月版）", "自治体公式Webページ", "https://www.city.hatsukaichi.hiroshima.jp/soshiki/31/78355.html", "2026", "資源ごみ(1)〜(5)を含む各正式名称と品目条件"),
        ("収集日一覧", "自治体公式Webページ", "https://www.city.hatsukaichi.hiroshima.jp/soshiki/31/12535.html", "現行案内中", "市内各地域で6種10分別が稼働すること"),
    ],
}

categories: list[dict[str,str]] = []

def add(mid: str, name: str, rep: str, *, source: int=1, parent: str="", ui: str="SORT_BUCKET",
        level: str="PRIMARY", channel: str="CURBSIDE", forbidden: str=NS, cond: str="", fallback: str=NS,
        prep: str=NS, bag: str="", size: str="", bulky: str="FALSE", note: str="") -> None:
    categories.append({
        "municipality_id":mid,"自治体正式名称":name,"category_group":parent or name,"parent_name":parent,
        "classification_level":level,"collection_channel":channel,"代表品目":rep,"入れてはいけない物":forbidden,
        "適用条件":cond,"条件外の扱い":fallback,"出す前の処理":prep,"袋・容器のルール":bag,
        "サイズ・条件":size,"粗大ごみ扱いか":bulky,"予約が必要か":"TRUE" if channel=="BOOKED_PICKUP" else "FALSE",
        "有料か":"FALSE","料金ルール":"","自治体収集外か":"FALSE","注意事項":note,"source_index":str(source),
        "出典ページ・該当箇所":name,"ui_role":ui,"rule_status":"CURRENT","effective_from":"","effective_to":"",
    })

# M095 Kure: 2026 calendar explicitly defines seven current collection labels.
add("M095","燃えるごみ","台所ごみ・紙くず・布類・草木等",prep="生ごみは水切り。市指定方法で出す")
add("M095","燃えないごみ","なべ・小型家電・陶磁器・ガラス類等",prep="電池を外し、危険物は安全に保護して出す")
add("M095","粗大ごみ","家具・寝具・ストーブ・自転車等",ui="REFERENCE_ONLY",bulky="TRUE",prep="市の粗大ごみ収集条件に従う")
add("M095","プラスチック資源","容器包装プラスチック・対象製品プラスチック",cond="令和8年4月開始の現行プラスチック資源",prep="汚れ等の市指定条件に従う")
add("M095","資源物（びん類・缶類・ペットボトル）","飲食用びん・缶・PETボトル",prep="中身を空にし、品目別の市指定方法で出す")
add("M095","資源物（紙類）","新聞・雑誌・段ボール等",prep="紙の種類ごとに市指定方法でまとめる")
add("M095","有害・危険ごみ","電池類・蛍光管・水銀体温計・スプレー缶・ライター等",prep="電池は絶縁等の市指定処理。スプレー缶等は中身を使い切る")

# M096 Takehara: five official resident categories.
add("M096","もやせる物","台所ごみ・紙くず・衣類布くず・木くず等",source=1,prep="生ごみは水切り。指定袋に入る衣類等はこの区分")
add("M096","リサイクルする物","ビン・カン・金属・陶磁器・ガラス・小型家電・ペットボトル",source=1,prep="中身を空にして品目別処理。スプレー缶は使い切り、穴を開ける必要はない")
add("M096","資源物","新聞・ちらし・雑誌・雑紙・書籍・紙パック・段ボール等",source=2,prep="紙の種類別に公式方法でまとめる")
add("M096","粗大ごみ","指定の大型家庭ごみ",source=1,ui="REFERENCE_ONLY",channel="BOOKED_PICKUP",bulky="TRUE",prep="申込制。現行は1回2品まで")
add("M096","有害ごみ","乾電池・ボタン電池・小型充電式電池・蛍光灯・ライター・充電池を外せない小型家電",source=1,prep="電池類等は安全措置を行い指定方法で出す")

# M097 Mihara: ten official divisions, with four leaves inside 発火性・有害ごみ.
add("M097","もやすごみ","生ごみ・紙くず・木くず等")
add("M097","不燃物","金属・汚れの落ちないびん缶・電化製品等",prep="電池を外し、外した電池は絶縁して電池区分へ")
add("M097","びん・飲料缶","飲料用びん・アルミ缶・スチール缶",prep="中身を除き水洗い")
add("M097","ペットボトル","PETマークのボトル",prep="キャップ・ラベルを外す")
add("M097","容器包装プラスチック","対象容器包装プラスチック",prep="汚れを落とす。PETのキャップ・ラベルはこちら")
add("M097","発火性危険ごみ","カセットボンベ・ガスライター・スプレー缶",prep="中身を使い切る。穴を開ける必要はない")
add("M097","電池","乾電池・ボタン電池・リチウム電池",prep="電極を色付きテープ等で絶縁")
add("M097","電池の外せない小型家電・充電式小型家電","ゲーム機・電気かみそり・電子たばこ・モバイルバッテリー等",prep="電池を外せない対象品を本体ごと出す")
add("M097","蛍光灯（有害ごみ）","蛍光灯・電球・水銀入り温度計等",prep="割れないよう箱または新聞紙等で保護")
add("M097","大型ごみ","予約対象の大型家庭ごみ",ui="REFERENCE_ONLY",channel="BOOKED_PICKUP",bulky="TRUE",prep="予約済表示をして出す")

# M100 Fuchu: five collection divisions; resource substreams remain internal conditions.
add("M100","可燃ごみ","台所ごみ・再生できない紙・木製品等",source=2,prep="市指定方法で出す")
add("M100","資源ごみ及び乾電池","びん・缶・古紙・古着・金属・小型家電・乾電池",source=2,prep="品目別に分ける。乾電池・モバイルバッテリーは絶縁し別袋。スプレー缶は中身を使い切り、穴を開けない")
add("M100","ペットボトル","飲料・酒類・調味料用PETボトル",source=1,prep="中をすすぎ、ふたを外す")
add("M100","埋立ごみ","陶器・ガラス・灰・傘等",source=1,prep="危険物は安全に保護し市指定袋で出す")
add("M100","容器包装プラスチックごみ","プラマークの容器包装",source=1,prep="中身を除き、洗って市指定袋で出す")

# M101 Miyoshi: exact nine regular collection categories.
for name, rep in [
    ("燃やせるごみ","家庭の可燃ごみ"),("プラスチック資源","対象プラスチック資源"),("紙資源","対象古紙"),
    ("資源物","びん・缶・PET等の資源物"),("布資源","対象古布・衣類"),("燃やせないごみ","不燃性家庭ごみ"),
    ("粗大ごみ","大型家庭ごみ"),("埋立ごみ","埋立対象ごみ"),("有害ごみ","電池・蛍光管等の有害物"),
]:
    add("M101",name,rep,source=1,ui="REFERENCE_ONLY" if name=="粗大ごみ" else "SORT_BUCKET",bulky="TRUE" if name=="粗大ごみ" else "FALSE",prep="市の区分別公式方法で出す")

# M103 Otake: eight numbered station streams + four official special routes.
for name, rep, prep in [
    ("もやすごみ","可燃性家庭ごみ","30cm未満等の市指定条件に従う"),
    ("プラスチックごみ","対象プラスチック製品・容器","洗浄等の市指定条件に従う"),
    ("紙資源","新聞・雑誌雑紙・段ボール","紙種類ごとにひもで十字に束ねる"),
    ("カン","飲食用缶・スプレー缶","中を空にする。スプレー缶等は必ず使い切る"),
    ("ビン","飲食用びん","中を空にして洗う"),
    ("ペットボトル","PETボトル","中を洗い、ラベルとキャップを外す"),
    ("衣類・毛布類","衣類・毛布・対象布製品","市指定方法で出す"),
    ("もやさないごみ","金属・陶磁器・ガラス・小型家電等","電池を外し、危険物は包み表示する"),
]: add("M103",name,rep,source=1,prep=prep)
add("M103","粗大ごみ","指定袋に入らない大型家庭ごみ",source=1,ui="REFERENCE_ONLY",channel="DIRECT_HAUL",bulky="TRUE",prep="予約してリサイクルセンターへ持ち込む")
add("M103","有害ごみ","蛍光管・水銀体温計・小型充電式電池・充電式小型家電等",source=1,ui="REFERENCE_ONLY",channel="DROP_OFF",prep="前日までに予約し資源回収専用袋等でリサイクルセンターへ持ち込む")
add("M103","電池類","マンガン・アルカリ・ボタン型電池等",source=1,ui="REFERENCE_ONLY",channel="DROP_OFF",prep="地区の使用済電池回収ボックスへ出す。必要に応じ絶縁")
add("M103","せん定枝","対象剪定枝",source=1,ui="REFERENCE_ONLY",channel="DROP_OFF",prep="長さ1m・太さ10cm以下にし、毎月第3木曜の予約受入へ")

# M104 Higashihiroshima: current eleven resident divisions.
for name, rep, prep, ui, bulky in [
    ("燃やせるごみ","紙・布・木くず・生ごみ・ゴム・皮類等","市指定オレンジ袋で出す","SORT_BUCKET","FALSE"),
    ("危険ごみ","陶磁器・ガラス・刃物・鏡類","危険物は安全に保護しオレンジ袋で出す","SORT_BUCKET","FALSE"),
    ("その他プラ","プラマークのないプラスチックのみの製品","紫色指定袋で出す","SORT_BUCKET","FALSE"),
    ("燃やせる粗大ごみ","家具・寝具・大型陶磁器・大型ガラス等","指定袋不要。市の粗大条件に従う","REFERENCE_ONLY","TRUE"),
    ("新聞","新聞・折込チラシ","種類別にまとめる","SORT_BUCKET","FALSE"),
    ("雑誌・雑がみ・ダンボール","雑誌・雑がみ・段ボール","種類別にまとめる","SORT_BUCKET","FALSE"),
    ("ビン・缶","びん類・缶類","中身を除き市指定方法で紫色袋へ","SORT_BUCKET","FALSE"),
    ("ペットボトル","PETマークのボトル","キャップ・ラベルを外し、市指定方法で紫色袋へ","SORT_BUCKET","FALSE"),
    ("リサイクルプラ","プラマークの容器包装","中身を使い切り軽くすすぐ。汚れが取れなければ燃やせるごみ","SORT_BUCKET","FALSE"),
    ("有害ごみ","蛍光管・白熱球・乾電池・ライター・小型充電式電池・水銀体温計等","電池は絶縁。蛍光管等は壊さず出す","SORT_BUCKET","FALSE"),
    ("燃やせない粗大ごみ","金物・家電・大型プラスチック・自転車等","指定袋不要。電池等を外す","REFERENCE_ONLY","TRUE"),
]: add("M104",name,rep,source=2,prep=prep,ui=ui,bulky=bulky)

# M105 Hatsukaichi: projection parent + five official resource leaves = 6種10分別.
add("M105","燃やせるごみ","30cm未満の可燃性家庭ごみ",source=1,bag="有料指定袋（黄色）",prep="生ごみは水切り。長さ条件に従う")
add("M105","資源ごみ","びん・かん・プラスチック容器・紙・布・剪定枝",source=1,level="PRIMARY")
for name, rep, prep in [
    ("資源ごみ(1) びん・かん類","飲食用びん・缶・スプレー缶","中を洗う。スプレー缶は屋外で中身を使い切り、穴を開ける必要はない"),
    ("資源ごみ(2) ペットボトルなどプラスチック製の容器（限定7品目）","PETボトル・対象プラスチック容器7品目","中を洗う。PETのふた・ラベルは燃やせるごみ"),
    ("資源ごみ(3) 紙類","新聞・雑誌・段ボール・紙パック・雑がみ","紙種別にまとめる。紙パックは洗い切り開いて乾かす"),
    ("資源ごみ(4) 布類","衣服・カーテン等","金具等を外し市指定方法で出す"),
    ("資源ごみ(5) 剪定枝","長さ1m以下・直径10cm以下の枝","5kg以内に束ね、ひもで縛る"),
]: add("M105",name,rep,source=2,parent="資源ごみ",ui="REFERENCE_ONLY",level="SUBCATEGORY",prep=prep)
add("M105","埋立ごみ","陶磁器・ガラス・埋立対象物",source=1,bag="指定袋（白）または土のう袋",prep="危険物は安全に保護して出す")
add("M105","大型ごみ","30cm以上等の大型家庭ごみ",source=1,ui="REFERENCE_ONLY",bulky="TRUE",prep="大型ごみ処分手数料納付券を貼る")
add("M105","小型および複雑ごみ","小型金属製品・複合素材品等",source=1,bag="指定袋（緑）",prep="電池等は外して指定区分へ")
add("M105","有害ごみ","電池・蛍光管・水銀製品・モバイルバッテリー等",source=1,prep="蛍光管は箱または結束。電池は安全措置を行う")


def ensure_deferred() -> None:
    path = MASTER / "05_deferred_municipalities.csv"
    fields, rows = read_csv(path)
    additions = {
        "M098": {"municipality_id":"M098","都道府県":"広島県","市町村":"尾道市","status":"DEFERRED","reason":"令和8年度に尾道・向島・御調・因島・瀬戸田の地域別CURRENT分別ガイドが併存し、住民向けcategory COREに差がある。現行municipality単位Schema/UIでは地域variantを安全に解決できないため一旦対象外。固定IDと公式根拠を保持する。","deferred_date":CHECKED,"decision_source":"SCHEMA_SCOPE_LIMITATION"},
        "M099": {"municipality_id":"M099","都道府県":"広島県","市町村":"福山市","status":"DEFERRED","reason":"市内一般は7種分別だが、令和8年度も内海町は分別体系が異なり、沼隈町も紙類の分別が異なることを市公式が明示。municipality単位Schema/UIで単一体系を適用すると誤案内になるため一旦対象外。","deferred_date":CHECKED,"decision_source":"SCHEMA_SCOPE_LIMITATION"},
    }
    existing = {r.get("municipality_id") for r in rows}
    for mid in sorted(DEFERRED):
        if mid not in existing:
            rows.append(additions[mid])
    rows.sort(key=lambda r:r.get("municipality_id",""))
    write_csv(path, fields, rows)


def ensure_registry() -> None:
    path = MASTER / "02_official_domain_registry.csv"
    fields, rows = read_csv(path)
    fields = fields or REGISTRY_FIELDS
    existing = {(r.get("municipality_id"),r.get("host")) for r in rows}
    for mid,specs in source_specs.items():
        for _,_,url,_,_ in specs:
            host=(urlparse(url).hostname or "").lower()
            if not host or (mid,host) in existing: continue
            rows.append({"municipality_id":mid,"host":host,"authority_type":"MUNICIPAL_DOMAIN","authority_name":municipality_specs[mid]["city"],"verification_url":municipality_specs[mid]["top"],"verified_date":CHECKED,"notes":"Batch 10 official source host"})
            existing.add((mid,host))
    rows.sort(key=lambda r:(r.get("municipality_id",""),r.get("host","")))
    write_csv(path, fields, rows)


def build_sources() -> list[dict[str,str]]:
    rows=[]
    for mid in sorted(TARGETS):
        for i,(title,kind,url,updated,used) in enumerate(source_specs[mid],1):
            rows.append({"municipality_id":mid,"source_id":f"S-{mid}-{i:02d}","資料名":title,"資料種別":kind,"公式URL":url,"発行主体":municipality_specs[mid]["city"],"対象年度":"令和8年度","ページ更新日":updated,"取得確認日":CHECKED,"使用した情報":used,"優先度":str(i),"現行性":"現行","備考":"","official_verified":"","official_basis":"","official_linking_url":""})
    return rows


def build_categories() -> list[dict[str,str]]:
    by_mid={}
    for raw in categories: by_mid.setdefault(raw["municipality_id"],[]).append(raw)
    rows=[]
    for mid in sorted(TARGETS):
        raws=by_mid[mid]
        name_to_id={r["自治体正式名称"]:f"C-{mid}-{i:02d}" for i,r in enumerate(raws,1)}
        for i,raw in enumerate(raws,1):
            sidx=int(raw["source_index"]); src=source_specs[mid][sidx-1]
            rows.append({"municipality_id":mid,"category_id":name_to_id[raw["自治体正式名称"]],"自治体正式名称":raw["自治体正式名称"],"category_group":raw["category_group"],"parent_category_id":name_to_id.get(raw["parent_name"],""),"classification_level":raw["classification_level"],"表示順":str(i),"collection_channel":raw["collection_channel"],"代表品目":raw["代表品目"],"入れてはいけない物":raw["入れてはいけない物"],"適用条件":raw["適用条件"],"条件外の扱い":raw["条件外の扱い"],"出す前の処理":raw["出す前の処理"],"袋・容器のルール":raw["袋・容器のルール"],"サイズ・条件":raw["サイズ・条件"],"粗大ごみ扱いか":raw["粗大ごみ扱いか"],"予約が必要か":raw["予約が必要か"],"有料か":raw["有料か"],"料金ルール":raw["料金ルール"],"自治体収集外か":raw["自治体収集外か"],"注意事項":raw["注意事項"],"source_id":f"S-{mid}-{sidx:02d}","出典URL":src[2],"出典ページ・該当箇所":raw["出典ページ・該当箇所"],"確認日":CHECKED,"ui_role":raw["ui_role"],"rule_status":raw["rule_status"],"effective_from":raw["effective_from"],"effective_to":raw["effective_to"]})
    return rows


def leaf_count(mid: str) -> int:
    raws=[r for r in categories if r["municipality_id"]==mid]
    parents={r["parent_name"] for r in raws if r["parent_name"]}
    return sum(1 for r in raws if r["自治体正式名称"] not in parents and r["ui_role"]!="EXCLUDED_NOTICE" and r["rule_status"]=="CURRENT")


def build_municipalities() -> list[dict[str,str]]:
    rows=[]
    official_counts={"M095":"7","M097":"10","M100":"5","M103":"12","M105":"10"}
    for mid in sorted(TARGETS):
        spec=municipality_specs[mid]; count=leaf_count(mid)
        status="OFFICIAL_COUNT_MATCHED" if mid in official_counts else "MANUAL_INDEX_REVIEW"
        rows.append({"municipality_id":mid,"都道府県":spec["pref"],"市町村":spec["city"],"実装区分":"中国5県全市町村","ごみ処理主体":spec["processor"],"自治体ごみトップURL":spec["top"],"分別ガイドURL":spec["guide"],"品目検索URL":"","やさしい日本語URL":"","多言語資料URL":"","対象年度":"令和8年度","最終確認日":CHECKED,"確認ステータス":"QA_REQUIRED","備考":spec["note"],"official_category_count":official_counts.get(mid,""),"reviewed_category_count":str(count),"category_count_basis":"住民が排出時に選択する現行公式分別区分を公式索引・現年度資料で全件照合。","category_count_verified":"TRUE","category_count_check_status":status,"category_count_review_id":f"CR-{mid}-CATEGORY-COVERAGE","category_count_reviewed_date":CHECKED,"category_count_reviewed_by":REVIEWER,"search_service_check_status":"NOT_CHECKED","search_service_check_evidence":"","easy_japanese_check_status":"NOT_CHECKED","easy_japanese_check_evidence":"","multilingual_check_status":"NOT_CHECKED","multilingual_check_evidence":""})
    return rows


def build_review_evidence() -> list[dict[str,str]]:
    rows=[]
    official={"M095","M097","M100","M103","M105"}
    for mid in sorted(TARGETS):
        for i,src in enumerate(source_specs[mid],1):
            role="OFFICIAL_TOTAL" if mid in official and i==1 else ("PRIMARY_INDEX" if i==1 else "SUPPLEMENTAL_INDEX")
            # For M100/M103/M105 exact total evidence is source 2/3 rather than source 1.
            if mid=="M100": role="OFFICIAL_TOTAL" if i==2 else ("PRIMARY_INDEX" if i==1 else "SUPPLEMENTAL_INDEX")
            if mid=="M103": role="OFFICIAL_TOTAL" if i==3 else ("PRIMARY_INDEX" if i==1 else "SUPPLEMENTAL_INDEX")
            if mid=="M105": role="OFFICIAL_TOTAL" if i==1 else ("SUPPLEMENTAL_INDEX")
            rows.append({"review_evidence_id":f"CRE-{mid}-{i:02d}","review_id":f"CR-{mid}-CATEGORY-COVERAGE","municipality_id":mid,"source_id":f"S-{mid}-{i:02d}","locator":src[4],"evidence_role":role,"notes":f"{CHECKED} Batch 10 resident-facing category completeness review"})
    return rows


def main() -> None:
    if set(municipality_specs)!=TARGETS or set(source_specs)!=TARGETS: raise ValueError("Batch10 active target mismatch")
    ensure_deferred(); ensure_registry(); OUT.mkdir(parents=True,exist_ok=True)
    p="batch_10_"
    write_csv(OUT/f"{p}municipalities.csv",MUNICIPALITY_FIELDS,build_municipalities())
    write_csv(OUT/f"{p}categories.csv",CATEGORY_FIELDS,build_categories())
    write_csv(OUT/f"{p}sources.csv",SOURCE_FIELDS,build_sources())
    write_csv(OUT/f"{p}qa.csv",QA_FIELDS,[])
    write_csv(OUT/f"{p}item_mapping.csv",MAPPING_FIELDS,[])
    write_csv(OUT/f"{p}item_coverage.csv",COVERAGE_FIELDS,[])
    write_csv(OUT/f"{p}category_review_evidence.csv",CATEGORY_REVIEW_EVIDENCE_FIELDS,build_review_evidence())
    counts=migrate_batch_dir(OUT)
    print(" ".join(f"{k}={v}" for k,v in counts.items()))

if __name__=="__main__": main()
