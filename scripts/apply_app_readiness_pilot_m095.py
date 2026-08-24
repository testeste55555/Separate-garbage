#!/usr/bin/env python3
"""Apply Kure City's complete 40-item APP readiness review."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from schema_v12 import (
    CATEGORY_FIELDS, COVERAGE_FIELDS, MAPPING_FIELDS, MUNICIPALITY_FIELDS,
    QA_FIELDS, SOURCE_FIELDS, compute_qa, read_csv, sync_municipality_qa_status,
    write_csv,
)

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "data/research"
MASTER = ROOT / "data/master"
AUDIT_PATH = RESEARCH / "app_readiness/m095_item_review.csv"
CHECKED = "2026-08-24"
REVIEWER = "OPENAI_CODEX_M095_APP_READINESS_V1"
MID = "M095"

AUDIT_FIELDS = [
    "municipality_id", "internal_item_id", "branch_order", "canonical_name",
    "display_name", "official_item_wording", "category_id", "category_name",
    "condition", "preparation", "exception_destination", "evidence_basis",
    "item_evidence_source_id", "item_evidence_url", "item_evidence_locator",
    "branch_review_status", "checked_date", "reviewer", "note",
]

@dataclass(frozen=True)
class Branch:
    category_id: str
    source_id: str
    locator: str
    wording: str
    condition: str
    preparation: str
    exception: str
    basis: str = "DIRECT_ITEM"

def b(spec: tuple[str, str, str, str, str, str, str, str]) -> Branch:
    return Branch(*spec)

URLS = {
    "S-M095-03": "https://www.city.kure.lg.jp/soshiki/19/gomidashinew-html.html",
    "S-M095-04": "https://www.city.kure.lg.jp/soshiki/18/kogatakaden-pc.html",
    "IS-M095-04": "https://www.city.kure.lg.jp/uploaded/attachment/109400.pdf",
    "IS-M095-05": "https://www.city.kure.lg.jp/soshiki/20/battery.html",
    "IS-M095-06": "https://www.city.kure.lg.jp/soshiki/18/haiki4-3r-kaden-pc.html",
    "IS-M095-07": "https://www.city.kure.lg.jp/soshiki/18/kogatakaden-pc.html",
    "IS-M095-08": "https://www.city.kure.lg.jp/soshiki/18/plastic-bunbetu.html",
    "IS-M095-09": "https://www.city.kure.lg.jp/uploaded/attachment/106973.pdf",
}

def source(source_id: str, title: str, used: str, source_type: str = "自治体公式Webページ") -> dict[str, str]:
    return {
        "municipality_id": MID, "source_id": source_id, "資料名": title,
        "資料種別": source_type, "公式URL": URLS[source_id], "発行主体": "呉市",
        "対象年度": "令和8年度／取得時点現行", "ページ更新日": "",
        "取得確認日": CHECKED, "使用した情報": used, "優先度": "1",
        "現行性": "CURRENT", "備考": "M095 40品目APP readiness手動レビューの公式根拠。",
        "official_verified": "TRUE", "official_basis": "MUNICIPAL_DOMAIN", "official_linking_url": "",
    }

NEW_SOURCES = [
    source("S-M095-03", "ごみ・資源物の出し方", "市で収集しないごみ・6区分・条件・例外"),
    source("S-M095-04", "使用済パソコン・小型家電の回収方法について", "小型家電回収ボックス経路・投入口条件"),
    source("IS-M095-04", "ごみ出し・分別あいうえお表（か音・現行PDF）", "傘・ガラス・刃物・乾電池・紙箱等の品目別ルール", "自治体公式PDF"),
    source("IS-M095-05", "小型充電式電池や乾電池・ボタン電池は有害・危険ごみです", "電池類・モバイルバッテリー・膨張変形品"),
    source("IS-M095-06", "家電リサイクル法対象品とパソコンの処分方法", "家電4品目・家庭用パソコン"),
    source("IS-M095-07", "使用済パソコン・小型家電の回収方法について", "小型家電・内蔵充電池・投入口40cm×20cm"),
    source("IS-M095-08", "令和8年4月からプラスチック資源の分別収集が始まります", "プラスチック資源の材質・汚れ・50cm条件"),
    source("IS-M095-09", "市政だよりくれ 令和8年1月号", "4月以降のPETフタ・ラベル、紙類・電池類の更新ルール", "自治体公式PDF"),
]

_RAW_BRANCHES = {'I001': [('C-M095-05', 'IS-M095-03', '資源物［ペットボトル］', 'ペットボトル', '飲料用・食品用のペットボトル', '中身を空にして軽く水洗いし、ラベルとフタを外して専用網袋へ入れる', '外したフタ・ラベルは2026年4月からプラスチック資源', 'DIRECT_ITEM')],
 'I002': [('C-M095-04', 'IS-M095-09', '市政だより令和8年1月号6頁「4月からペットボトルのふたとラベルはプラスチック資源へ」', 'ペットボトルのフタ', 'ペットボトルから外したプラスチック製フタ', '本体から外し、汚れを落としてプラスチック資源専用指定袋へ入れる', '汚れが落ちない物は燃えるごみ', 'DIRECT_ITEM')],
 'I003': [('C-M095-04', 'IS-M095-09', '市政だより令和8年1月号6頁「4月からペットボトルのふたとラベルはプラスチック資源へ」', 'ペットボトルのラベル', 'ペットボトルから外したプラスチック製ラベル', '本体から外し、汚れを落としてプラスチック資源専用指定袋へ入れる', '汚れが落ちない物は燃えるごみ', 'DIRECT_ITEM')],
 'I004': [('C-M095-05', 'IS-M095-03', '資源物［缶類］', 'アルミ缶', '飲料・食品用のアルミ缶', '中身を全部取り除いて軽く水洗いし、袋から出して専用網袋へ入れる', '汚れや臭いが取れない物・腐敗した物は燃えないごみ', 'DIRECT_ITEM')],
 'I005': [('C-M095-05', 'IS-M095-03', '資源物［缶類］', 'スチール缶', '飲料・食品用のスチール缶', '中身を全部取り除いて軽く水洗いし、袋から出して専用網袋へ入れる', '汚れや臭いが取れない物・腐敗した物は燃えないごみ', 'DIRECT_ITEM')],
 'I006': [('C-M095-05', 'IS-M095-04', 'か音50音表「ガラスびん（飲料用，食品用）」', 'ガラスびん（飲料用・食品用）', '飲料・食品用のガラスびん', 'フタを取り、中身を空にして軽く水洗いし、無色透明・茶色・その他の色に分けて各コンテナへ入れる', '乳白色・汚れがひどい物・割れた物は燃えないごみ', 'DIRECT_ITEM'),
          ('C-M095-02', 'IS-M095-04', 'か音50音表「ガラスびん（飲料用，食品用以外）」', '飲料・食品用以外のガラスびん', '飲料・食品用以外のガラスびん、乳白色びん、汚れがひどい又は割れたびん', '割れや欠けがある場合は丈夫な紙などで包み、燃えないごみの指定袋へ入れる', '飲料・食品用で状態の良いびんは資源物', 'DIRECT_ITEM')],
 'I007': [('C-M095-04', 'IS-M095-09', '市政だより令和8年1月号4頁「トレイ類」', '白色食品トレイ', 'プラスチックだけでできた50cm未満の白色食品トレイで汚れが落ちる物', '中身を除き軽く水洗いし、プラスチック資源専用指定袋へ入れる', '汚れが落ちない物は燃えるごみ', 'DIRECT_ITEM'),
          ('C-M095-01', 'IS-M095-08', 'プラスチック資源「水洗いしても汚れが落ちないもの」', '汚れが落ちない白色食品トレイ', '水洗いしても食品汚れが落ちない白色食品トレイ', '中身を空にし、燃えるごみの指定袋へ入れる', '汚れが落ちる物はプラスチック資源', 'OFFICIAL_RULE_DERIVED')],
 'I008': [('C-M095-04', 'IS-M095-08', 'プラスチック資源の対象条件', '色柄食品トレイ', 'プラスチックだけでできた50cm未満の色柄食品トレイで汚れが落ちる物', '中身を除き軽く水洗いし、プラスチック資源専用指定袋へ入れる', '汚れが落ちない物は燃えるごみ', 'OFFICIAL_RULE_DERIVED'),
          ('C-M095-01', 'IS-M095-08', 'プラスチック資源「水洗いしても汚れが落ちないもの」', '汚れが落ちない色柄食品トレイ', '水洗いしても食品汚れが落ちない色柄食品トレイ', '中身を空にし、燃えるごみの指定袋へ入れる', '汚れが落ちる物はプラスチック資源', 'OFFICIAL_RULE_DERIVED')],
 'I009': [('C-M095-04', 'IS-M095-08', 'プラスチック資源の対象条件', 'プラスチック製弁当容器', 'プラスチックだけでできた50cm未満の弁当容器で汚れが落ちる物', '中身を除き軽く水洗いし、プラスチック資源専用指定袋へ入れる', '汚れが落ちない物は燃えるごみ', 'OFFICIAL_RULE_DERIVED'),
          ('C-M095-01', 'IS-M095-08', 'プラスチック資源「水洗いしても汚れが落ちないもの」', '汚れが落ちない弁当容器', '水洗いしても食品汚れが落ちないプラスチック製弁当容器', '中身を空にし、燃えるごみの指定袋へ入れる', '汚れが落ちる物はプラスチック資源', 'OFFICIAL_RULE_DERIVED')],
 'I010': [('C-M095-04', 'IS-M095-08', 'プラスチック資源の対象条件', 'プラスチック製菓子袋', 'プラスチックだけでできた菓子袋で汚れが落ちる物', '中身を空にし、必要に応じて軽く水洗いしてプラスチック資源専用指定袋へ入れる', '汚れが落ちない物は燃えるごみ', 'OFFICIAL_RULE_DERIVED'),
          ('C-M095-01', 'IS-M095-08', 'プラスチック資源「汚れが落ちないもの」', '汚れが落ちない菓子袋', '食品汚れが落ちないプラスチック製菓子袋', '中身を空にし、燃えるごみの指定袋へ入れる', '汚れが落ちる物はプラスチック資源', 'OFFICIAL_RULE_DERIVED')],
 'I011': [('C-M095-04', 'IS-M095-08', 'プラスチック資源の対象条件', 'レジ袋', 'プラスチックだけでできた50cm未満の清潔なレジ袋', '内容物を除き、プラスチック資源専用指定袋へ入れる', '汚れが落ちない物は燃えるごみ', 'OFFICIAL_RULE_DERIVED'),
          ('C-M095-01', 'IS-M095-08', 'プラスチック資源「汚れが落ちないもの」', '汚れが落ちないレジ袋', '汚れが落ちないプラスチック製レジ袋', '内容物を除き、燃えるごみの指定袋へ入れる', '清潔な物はプラスチック資源', 'OFFICIAL_RULE_DERIVED')],
 'I012': [('C-M095-04', 'IS-M095-09', '市政だより令和8年1月号4頁「発泡スチロール製の食品トレイ・緩衝材」', '発泡スチロール', 'プラスチックだけでできた50cm未満の発泡スチロールで汚れが落ちる物', 'テープ等の異物を外し、必要に応じて洗ってプラスチック資源専用指定袋へ入れる', '汚れが落ちない物は燃えるごみ。50cm以上で小さくできない物は粗大ごみ', 'DIRECT_ITEM'),
          ('C-M095-01', 'IS-M095-08', 'プラスチック資源「水洗いしても汚れが落ちないもの」', '汚れが落ちない発泡スチロール', '水洗いしても汚れが落ちない発泡スチロール', '異物を除き、燃えるごみの指定袋へ入れる', '汚れが落ちる50cm未満はプラスチック資源', 'OFFICIAL_RULE_DERIVED'),
          ('C-M095-03', 'IS-M095-08', 'プラスチック資源「50cm以上で小さくすることが難しいもの」', '大型の発泡スチロール', '1辺50cm以上で50cm未満へ小さくすることが難しい発泡スチロール', '粗大ごみ処理券を付けて粗大ごみとして出す', '50cm未満にできる物はプラスチック資源', 'OFFICIAL_RULE_DERIVED')],
 'I013': [('C-M095-06', 'IS-M095-03', '資源物［紙類］新聞紙', '新聞', '新聞紙・広告・チラシ', '新聞類だけでまとめ、ひもで十文字に縛る', '汚れたり濡れたりして再生できない紙は燃えるごみ', 'DIRECT_ITEM'),
          ('C-M095-01', 'IS-M095-04', 'か音50音表「紙類・厚紙」注意事項', '汚れ・濡れのある新聞', '汚れたり濡れたりして再生できない新聞紙', '燃えるごみの指定袋へ入れる', '清潔で乾いた新聞は資源物（紙類）', 'OFFICIAL_RULE_DERIVED')],
 'I014': [('C-M095-06', 'IS-M095-03', '資源物［紙類］段ボール', '段ボール', '家庭から出る清潔で乾いた段ボール', '折りたたみ、段ボールだけでひもを十文字に縛る', '汚れたり濡れたりして再生できない物は燃えるごみ', 'DIRECT_ITEM'),
          ('C-M095-01', 'IS-M095-04', 'か音50音表「紙類・厚紙」注意事項', '汚れ・濡れのある段ボール', '汚れたり濡れたりして再生できない段ボール', '燃えるごみの指定袋へ入れる', '清潔で乾いた段ボールは資源物（紙類）', 'OFFICIAL_RULE_DERIVED')],
 'I015': [('C-M095-06', 'IS-M095-03', '資源物［紙類］本・雑誌', '雑誌', '清潔で乾いた本・雑誌', '雑誌類だけでまとめ、ひもで十文字に縛る', '汚れ・濡れ・感熱紙等の再生できない紙は燃えるごみ', 'DIRECT_ITEM'),
          ('C-M095-01', 'IS-M095-04', 'か音50音表「紙類・厚紙」注意事項', '再生できない雑誌・紙', '汚れたり濡れたりして再生できない雑誌・紙類', '燃えるごみの指定袋へ入れる', '清潔で再生可能な雑誌は資源物（紙類）', 'OFFICIAL_RULE_DERIVED')],
 'I016': [('C-M095-06', 'IS-M095-04', 'か音50音表「菓子箱（紙）」', '菓子箱・雑紙', '清潔で乾いた紙製の菓子箱・包装紙等', '異物を外し、紙類としてひもで十文字に縛る', '汚れ・臭いが取れない物、濡れた物は燃えるごみ', 'DIRECT_ITEM'),
          ('C-M095-01', 'IS-M095-04', 'か音50音表「菓子箱（紙）」注意事項', '汚れ・濡れのある紙箱', '汚れ・臭いが取れない又は濡れた紙箱・雑紙', '燃えるごみの指定袋へ入れる', '清潔で乾いた紙箱は資源物（紙類）', 'DIRECT_ITEM')],
 'I017': [('C-M095-06', 'IS-M095-03', '資源物［紙類］紙パック', '紙パック', '内側にアルミ箔がない飲料用紙パック', '切り開き、軽く水洗いして乾燥させ、紙パックだけでひもを十文字に縛る', 'アルミ箔付き紙パックは燃えないごみ', 'DIRECT_ITEM'),
          ('C-M095-02', 'IS-M095-09', '市政だより令和8年1月号6頁「アルミ箔のついた紙パックは燃えないごみへ」', 'アルミ箔付き紙パック', '内側などにアルミ箔が付いた紙パック', '中身を空にし、燃えないごみの指定袋へ入れる', 'アルミ箔のない紙パックは資源物（紙類）', 'DIRECT_ITEM')],
 'I018': [('C-M095-01', 'IS-M095-03', '燃えるごみ「料理くず、残飯」', '生ごみ', '家庭の料理くず・残飯等', '水気を十分に切り、燃えるごみの指定袋へ入れる', '多量に一時排出する場合は通常収集に出さず自己搬入等', 'DIRECT_ITEM')],
 'I019': [('C-M095-01', 'IS-M095-03', '燃えるごみ「再生できない紙くず」', '使用済みティッシュ', '使用済みティッシュなど再生できない汚れた紙', '衛生上必要なら小袋にまとめ、燃えるごみの指定袋へ入れる', '資源化できる清潔な紙類は資源物（紙類）', 'OFFICIAL_RULE_DERIVED')],
 'I020': [('C-M095-01', 'IS-M095-03', '燃えるごみ「おむつは、汚物を取り除いて丈夫な袋」', '紙おむつ', '家庭から出る使用済み紙おむつ', '汚物を取り除き、丈夫な袋に入れてから燃えるごみの指定袋へ入れる', '汚物そのものはごみステーションに出さない', 'DIRECT_ITEM')],
 'I021': [('C-M095-01', 'IS-M095-03', '燃えるごみ「再利用できない衣服など（少量）」', '衣類', '再利用できない衣類を少量出す場合', '燃えるごみの指定袋へ入れる', '再利用できる布類は資源集団回収・衣料品等拠点回収を優先', 'DIRECT_ITEM')],
 'I022': [('C-M095-02', 'IS-M095-04', 'か音50音表「傘・日傘・ビニール傘」', '傘・日傘・ビニール傘', '家庭用の傘', '燃えないごみ指定袋【大】に入れて口を閉じる。傘が袋から出てもよい', '傘立て等は大きさにより粗大ごみとなるが、傘自体はこの扱い', 'DIRECT_ITEM')],
 'I023': [('C-M095-02', 'IS-M095-03', '燃えないごみ「せともの類」', '陶磁器', '家庭用の陶磁器・せともの', '割れや欠けで危険な場合は丈夫な紙等で包み、燃えないごみの指定袋へ入れる', '指定袋に入らない大型品は粗大ごみの基準を確認', 'DIRECT_ITEM')],
 'I024': [('C-M095-02', 'IS-M095-04', 'か音50音表「ガラス類（食器等）」', 'ガラス製品', '飲料・食品びん以外のガラス食器・製品', '割れや欠けがある場合は丈夫な紙などで包み、燃えないごみの指定袋へ入れる', '飲料・食品用びんは資源物', 'DIRECT_ITEM')],
 'I025': [('C-M095-02', 'IS-M095-03', '燃えないごみ「ガラスなど割れやすいもの」', '割れたガラス', '割れたガラス・ガラス製品', '丈夫な布や紙にしっかり包み、燃えないごみの指定袋へ入れる', '割れていない飲料・食品用びんは資源物', 'DIRECT_ITEM')],
 'I026': [('C-M095-02', 'IS-M095-04', 'か音50音表「カミソリの刃」及び燃えないごみの刃物ルール', '包丁・刃物', '家庭用の包丁・刃物', '丈夫な紙・布で刃をしっかり包み、内容物が分かるようにして燃えないごみへ出す', '大型の刃物等で指定袋条件外の場合は市へ確認', 'DIRECT_ITEM')],
 'I027': [('C-M095-07', 'IS-M095-05', '小型充電式電池や乾電池・ボタン電池は有害・危険ごみ', '乾電池', '家庭から出る乾電池', '他のごみと混ぜず、有害・危険ごみとして赤いコンテナへ入れる', '膨張・変形したリチウム系電池は環境施設課窓口へ直接持参', 'DIRECT_ITEM')],
 'I028': [('C-M095-07', 'IS-M095-05', '小型充電式電池や乾電池・ボタン電池は有害・危険ごみ', 'ボタン電池', '家庭から出るボタン電池', '他のごみと混ぜず、有害・危険ごみとして赤いコンテナへ入れる', '膨張・変形したリチウム系電池は環境施設課窓口へ直接持参', 'DIRECT_ITEM')],
 'I029': [('C-M095-07', 'IS-M095-05', '2026年5月20日更新「モバイルバッテリー」・膨張変形品の扱い', 'モバイルバッテリー', '膨張・変形していない家庭用モバイルバッテリー', '他のごみと混ぜず、有害・危険ごみとして回収へ出す', '膨張・変形した物は環境施設課窓口で職員へ直接渡す', 'DIRECT_ITEM')],
 'I030': [('C-M095-07', 'IS-M095-03', '有害・危険ごみ「蛍光管（割れていないもの）」', '蛍光管', '割れていない蛍光管', '割れないよう保護し、有害・危険ごみの赤いコンテナへ入れる', '割れた蛍光管は燃えないごみ', 'DIRECT_ITEM'),
          ('C-M095-02', 'IS-M095-03', '有害・危険ごみ注記「割れた蛍光管は燃えないごみ」', '割れた蛍光管', '割れた蛍光管', '破片が散らないよう安全に包み、燃えないごみとして出す', '割れていない蛍光管は有害・危険ごみ', 'DIRECT_ITEM')],
 'I031': [('C-M095-02', 'IS-M095-03', '有害・危険ごみ注記「電球、LED電灯は燃えないごみ」', '電球・LED電灯', '白熱電球・LED電球等', '割れないよう扱い、燃えないごみの指定袋へ入れる', '蛍光管は割れていなければ有害・危険ごみ', 'DIRECT_ITEM')],
 'I032': [('C-M095-07', 'IS-M095-03', '有害・危険ごみ「スプレー缶」', 'スプレー缶', '家庭から出るスプレー缶', '穴を開けず、そのまま有害・危険ごみの赤いコンテナへ入れる', '中身が残っている場合も穴を開けずそのまま出せる', 'DIRECT_ITEM')],
 'I033': [('C-M095-07', 'IS-M095-03', '有害・危険ごみ「使い捨てライター」', '使い捨てライター', '家庭から出る使い捨てライター', '他のごみと混ぜず、有害・危険ごみの赤いコンテナへ入れる', '燃えないごみ・粗大ごみには混ぜない', 'DIRECT_ITEM')],
 'I034': [('C-M095-02', 'IS-M095-07', '小型家電回収「回収対象」及び燃えないごみの小型家電', '小型家電', '電池を取り外せる小型家電で燃えないごみ指定袋に入る物', '電池・バッテリーを外し、本体を燃えないごみへ。40cm×20cm投入口に入る物は小型家電回収ボックスも利用可', '外した電池は有害・危険ごみ。内蔵充電池を外せない物は小型家電回収ボックス', 'DIRECT_ITEM')],
 'I035': [('C-M095-09', 'IS-M095-07', '回収ボックスに出せないもの注記「電池が外せない場合はそのまま小型家電回収ボックス」', '充電池を外せない小型家電', '充電式電池が内蔵され、電池を取り外せない小型家電', '燃えないごみ・粗大ごみに出さず、そのまま40cm×20cm投入口の小型家電回収ボックスへ入れる', '家電4品目は回収ボックス対象外。膨張・変形電池は環境施設課へ相談', 'DIRECT_ITEM')],
 'I036': [('C-M095-03', 'IS-M095-03', '粗大ごみ「寝具類（掛けふとん、敷きふとん）」', '布団', '掛け布団・敷き布団など指定袋に入らない寝具', 'ひもで縛り、粗大ごみ処理券を付けて出す', '長さ2m以上の物は原則シール2枚。品目別例外は50音表で確認', 'DIRECT_ITEM')],
 'I037': [('C-M095-08', 'IS-M095-06', '家電4品目の処分方法', '家電4品目', 'エアコン・テレビ・冷蔵庫／冷凍庫・洗濯機／衣類乾燥機', '販売店へ引取りを依頼するか、家電リサイクル券を用意して指定引取場所へ持ち込む', 'ごみステーション・粗大ごみ・小型家電回収ボックスには出さない', 'DIRECT_ITEM')],
 'I038': [('C-M095-08', 'IS-M095-06', '家庭用パソコンの処分方法', '家庭用パソコン', '家庭用パソコン・ディスプレイ', 'ごみステーションには出さず、宅配回収、小型家電回収ボックス（入る場合）、メーカー又はパソコン3R協会の回収を利用する', '家電4品目とは別のPCリサイクル経路', 'DIRECT_ITEM')],
 'I039': [('C-M095-01', 'IS-M095-03', '燃えるごみ「油は、紙などに十分吸わせて」', '使用済み食用油', '家庭で使用した食用油', '紙などに十分吸わせ、漏れないようにして燃えるごみへ出す', '廃油など市で処理できない種類は販売店等へ相談', 'DIRECT_ITEM')],
 'I040': [('C-M095-01', 'IS-M095-03', '燃えるごみ「板きれ、棒きれなどは長さ50cm以下」', '少量の剪定枝', '家庭から少量出る、長さ50cm以下にできる剪定枝・枝木', '長さ50cm以下に切り、燃えるごみとして出す', '一時に多量となる庭木の剪定ごみは通常収集に出さず自己搬入又は許可業者へ依頼', 'OFFICIAL_RULE_DERIVED'),
          ('C-M095-08', 'IS-M095-03', '市で収集しないごみ「多量ごみ等：庭木の剪定」', '多量の剪定枝', '庭木の剪定等で一時に多量に出る枝木', 'ごみステーションに出さず、自分で処理施設へ搬入（有料）するか許可業者へ依頼する', '少量で通常条件に収まる枝木は燃えるごみ', 'DIRECT_ITEM'),
          ('C-M095-08', 'IS-M095-03', '市で処理できないごみ「直径10cm又は10cm角・長さ1.5mを超える木くず」', '処理寸法を超える木くず', '直径10cm又は10cm角、又は長さ1.5mを超える木くず・伐採木', '販売店へ相談するか、市の許可を受けた一般廃棄物処理業者へ依頼する', '規格内で少量の枝木は燃えるごみ', 'DIRECT_ITEM')]}
BRANCHES: dict[str, list[Branch]] = {iid: [b(spec) for spec in specs] for iid, specs in _RAW_BRANCHES.items()}

def excluded_category() -> dict[str, str]:
    return {
        "municipality_id": MID, "category_id": "C-M095-08", "自治体正式名称": "市で収集しないごみ",
        "category_group": "市で収集しないごみ", "parent_category_id": "", "classification_level": "EXCLUDED",
        "表示順": "8", "collection_channel": "NOT_COLLECTED",
        "代表品目": "家電4品目・家庭用パソコン・多量ごみ・市で処理できないごみ",
        "入れてはいけない物": "通常の市収集対象ごみ", "適用条件": "市が収集しない又は処理できない指定品",
        "条件外の扱い": "品目ごとの通常収集区分", "出す前の処理": "販売店・指定回収経路・自己搬入・許可業者等を確認",
        "袋・容器のルール": "市指定袋へ入れない", "サイズ・条件": "家電リサイクル法対象品・PC・多量ごみ・処理困難物等",
        "粗大ごみ扱いか": "FALSE", "予約が必要か": "CONDITIONAL", "有料か": "CONDITIONAL",
        "料金ルール": "回収経路・品目により異なる", "自治体収集外か": "TRUE",
        "注意事項": "通常のごみステーションへ出さず、品目別の指定経路を利用",
        "source_id": "S-M095-03", "出典URL": URLS["S-M095-03"], "出典ページ・該当箇所": "市で収集しないごみ",
        "確認日": CHECKED, "ui_role": "EXCLUDED_NOTICE", "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
    }

def small_appliance_category() -> dict[str, str]:
    return {
        "municipality_id": MID, "category_id": "C-M095-09", "自治体正式名称": "小型家電回収ボックス",
        "category_group": "小型家電回収", "parent_category_id": "", "classification_level": "ALTERNATIVE",
        "表示順": "9", "collection_channel": "DROP_OFF",
        "代表品目": "投入口40cm×20cmに入る小型家電・電池を外せない充電式小型家電",
        "入れてはいけない物": "家電リサイクル法対象4品目・外せる乾電池や小型充電式電池・電球・蛍光灯",
        "適用条件": "家庭から排出され、回収ボックス投入口40cm×20cmに入る対象小型家電",
        "条件外の扱い": "通常の燃えないごみ、家電リサイクル、又は品目別指定経路",
        "出す前の処理": "個人情報を消去。外せる電池は外して有害・危険ごみへ",
        "袋・容器のルール": "回収ボックスへ直接投入", "サイズ・条件": "投入口40cm×20cm",
        "粗大ごみ扱いか": "FALSE", "予約が必要か": "FALSE", "有料か": "FALSE",
        "料金ルール": "", "自治体収集外か": "FALSE",
        "注意事項": "充電池を外せない小型家電はそのまま回収ボックスへ",
        "source_id": "S-M095-04", "出典URL": URLS["S-M095-04"], "出典ページ・該当箇所": "市内18箇所でボックス回収／回収対象・対象外",
        "確認日": CHECKED, "ui_role": "REFERENCE_ONLY", "rule_status": "CURRENT", "effective_from": "", "effective_to": "",
    }

def main() -> None:
    _, items = read_csv(MASTER / "04_common_items_master.csv")
    _, municipalities = read_csv(RESEARCH / "04_municipalities_research.csv")
    _, categories = read_csv(RESEARCH / "02_categories_master.csv")
    _, sources = read_csv(RESEARCH / "03_sources_master.csv")
    _, qa = read_csv(RESEARCH / "06_qa_log.csv")
    _, review_evidence = read_csv(RESEARCH / "08_category_review_evidence.csv")
    _, mappings = read_csv(RESEARCH / "05_item_mapping_master.csv")
    _, coverage = read_csv(RESEARCH / "07_item_mapping_coverage.csv")

    expected_items = {f"I{i:03d}" for i in range(1, 41)}
    assert set(BRANCHES) == expected_items and all(BRANCHES.values())
    item_by = {r["internal_item_id"]: r for r in items}

    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    for row in NEW_SOURCES:
        source_by[(MID, row["source_id"])] = row
    sources = sorted(source_by.values(), key=lambda r: (r["municipality_id"], r["source_id"]))
    source_by = {(r["municipality_id"], r["source_id"]): r for r in sources}
    for sid, url in URLS.items():
        row = source_by[(MID, sid)]
        assert row["公式URL"] == url and row["official_verified"] == "TRUE"

    category_by = {(r["municipality_id"], r["category_id"]): r for r in categories}
    category_by[(MID, "C-M095-08")] = excluded_category()
    category_by[(MID, "C-M095-09")] = small_appliance_category()
    categories = sorted(category_by.values(), key=lambda r: (r["municipality_id"], r["category_id"]))
    category_by = {(r["municipality_id"], r["category_id"]): r for r in categories}

    existing_by_pair: dict[str, list[dict[str, str]]] = {}
    for row in mappings:
        if row["municipality_id"] == MID:
            existing_by_pair.setdefault(row["internal_item_id"], []).append(row)
    for rows in existing_by_pair.values():
        rows.sort(key=lambda r: (int(r.get("branch_order") or 0), r["mapping_id"]))

    retained = [r for r in mappings if r["municipality_id"] != MID]
    used_ids = {r["mapping_id"] for r in retained}
    generated: list[dict[str, str]] = []
    audit: list[dict[str, str]] = []
    for iid in sorted(expected_items):
        old = existing_by_pair.get(iid, [])
        for order, spec in enumerate(BRANCHES[iid], start=1):
            category = category_by[(MID, spec.category_id)]
            evidence = source_by[(MID, spec.source_id)]
            mapping_id = old[order - 1]["mapping_id"] if order <= len(old) else f"MAP-{MID}-{iid}-APP-{order:02d}"
            assert mapping_id not in used_ids
            used_ids.add(mapping_id)
            row = {field: "" for field in MAPPING_FIELDS}
            row.update({
                "mapping_id": mapping_id, "municipality_id": MID, "internal_item_id": iid, "branch_order": str(order),
                "自治体での品目表記": spec.wording, "category_id": spec.category_id,
                "分別区分正式名称": category["自治体正式名称"], "条件": spec.condition, "前処理": spec.preparation,
                "例外分別先": spec.exception, "自治体収集外": category["自治体収集外か"], "rule_status": category["rule_status"],
                "effective_from": category["effective_from"], "effective_to": category["effective_to"],
                "category_source_id": category["source_id"], "category_source_url": category["出典URL"],
                "category_source_locator": category["出典ページ・該当箇所"], "item_evidence_source_id": spec.source_id,
                "item_evidence_url": evidence["公式URL"], "item_evidence_locator": spec.locator, "確認日": CHECKED,
                "mapping_status": "APP_READY", "evidence_scope": "ITEM_SPECIFIC", "branch_review_status": "COMPLETE",
                "reviewed_date": CHECKED, "reviewed_by": REVIEWER,
                "備考": f"M095 40品目APP readiness手動レビュー。{spec.basis}。",
            })
            generated.append(row)
            item = item_by[iid]
            audit.append({
                "municipality_id": MID, "internal_item_id": iid, "branch_order": str(order),
                "canonical_name": item["一般管理用名称"], "display_name": item["教材表示名"],
                "official_item_wording": spec.wording, "category_id": spec.category_id,
                "category_name": category["自治体正式名称"], "condition": spec.condition,
                "preparation": spec.preparation, "exception_destination": spec.exception,
                "evidence_basis": spec.basis, "item_evidence_source_id": spec.source_id,
                "item_evidence_url": evidence["公式URL"], "item_evidence_locator": spec.locator,
                "branch_review_status": "COMPLETE", "checked_date": CHECKED, "reviewer": REVIEWER,
                "note": "公式品目行又は現行公式ルールから条件枝を手動照合。",
            })

    mappings = sorted(retained + generated, key=lambda r: (r["municipality_id"], r["internal_item_id"], int(r.get("branch_order") or 0), r["mapping_id"]))
    coverage_by = {(r["municipality_id"], r["internal_item_id"]): r for r in coverage}
    for iid in sorted(expected_items):
        first = BRANCHES[iid][0]
        evidence = source_by[(MID, first.source_id)]
        coverage_by[(MID, iid)].update({
            "coverage_status": "APP_READY", "mapping_branch_count": str(len(BRANCHES[iid])),
            "branch_completeness_confirmed": "TRUE", "evidence_scope": "ITEM_SPECIFIC",
            "item_evidence_source_id": first.source_id, "item_evidence_url": evidence["公式URL"],
            "item_evidence_locator": first.locator, "reviewed_date": CHECKED, "reviewed_by": REVIEWER,
            "notes": "M095の全40品目・全条件枝を現行公式資料へ手動照合し、自治体単位でatomic APP_READY昇格。",
        })
    coverage = sorted(coverage_by.values(), key=lambda r: (r["municipality_id"], r["internal_item_id"]))

    batch = RESEARCH / "batches/batch_10"
    _, batch_municipalities = read_csv(batch / "batch_10_municipalities.csv")
    _, batch_categories = read_csv(batch / "batch_10_categories.csv")
    _, batch_sources = read_csv(batch / "batch_10_sources.csv")
    _, batch_qa = read_csv(batch / "batch_10_qa.csv")
    _, batch_review_evidence = read_csv(batch / "batch_10_category_review_evidence.csv")
    batch_category_by = {(r["municipality_id"], r["category_id"]): r for r in batch_categories}
    batch_category_by[(MID, "C-M095-08")] = excluded_category()
    batch_category_by[(MID, "C-M095-09")] = small_appliance_category()
    batch_categories = sorted(batch_category_by.values(), key=lambda r: (r["municipality_id"], r["category_id"]))
    batch_source_by = {(r["municipality_id"], r["source_id"]): r for r in batch_sources}
    batch_source_by[(MID, "S-M095-03")] = source_by[(MID, "S-M095-03")]
    batch_source_by[(MID, "S-M095-04")] = source_by[(MID, "S-M095-04")]
    batch_sources = sorted(batch_source_by.values(), key=lambda r: (r["municipality_id"], r["source_id"]))
    batch_qa = compute_qa(batch_municipalities, batch_categories, batch_sources, batch_review_evidence, batch_qa)
    batch_municipalities = sync_municipality_qa_status(batch_municipalities, batch_qa)

    qa = compute_qa(municipalities, categories, sources, review_evidence, qa)
    municipalities = sync_municipality_qa_status(municipalities, qa)
    write_csv(RESEARCH / "02_categories_master.csv", CATEGORY_FIELDS, categories)
    write_csv(RESEARCH / "03_sources_master.csv", SOURCE_FIELDS, sources)
    write_csv(RESEARCH / "04_municipalities_research.csv", MUNICIPALITY_FIELDS, municipalities)
    write_csv(RESEARCH / "05_item_mapping_master.csv", MAPPING_FIELDS, mappings)
    write_csv(RESEARCH / "06_qa_log.csv", QA_FIELDS, qa)
    write_csv(RESEARCH / "07_item_mapping_coverage.csv", COVERAGE_FIELDS, coverage)
    write_csv(AUDIT_PATH, AUDIT_FIELDS, audit)
    write_csv(batch / "batch_10_municipalities.csv", MUNICIPALITY_FIELDS, batch_municipalities)
    write_csv(batch / "batch_10_categories.csv", CATEGORY_FIELDS, batch_categories)
    write_csv(batch / "batch_10_sources.csv", SOURCE_FIELDS, batch_sources)
    write_csv(batch / "batch_10_qa.csv", QA_FIELDS, batch_qa)
    print(f"M095_APP_READINESS_APPLIED items=40 branches={len(generated)} app_ready_pairs=40 sources_added={len(NEW_SOURCES)} references_added=2")

if __name__ == "__main__":
    main()
