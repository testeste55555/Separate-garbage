# Separate-garbage

技能実習生等を対象とした、自治体別ごみ分別学習アプリのプロジェクトです。

## Can-do

> 名前が分からないごみでも、自分が住む自治体のルールを調べて、仲間と相談しながら、正しく分別ができる。

## 設計原則

- ごみ名称の暗記を主目的にしない。
- 各自治体の公式な分別名称・分別ルールを保持する。
- 自治体公式情報を一次情報として扱う。
- 収集曜日・収集時間・地区別カレンダーは本プロジェクトの主対象外とする。
- 原典、構造化データ、アプリ用加工データを分離する。
- 不明情報を推測で埋めない。

## ディレクトリ

- `data/master/` : 実装対象自治体MASTER
- `data/research/` : 自治体ごとの調査・構造化データ
- `data/app/` : アプリ投入用の加工済みデータ
- `docs/workflow/` : WORK用フロー・調査手順
- `docs/schema/` : スキーマ、データ辞書、QA仕様
- `app/` : Webアプリ本体
- `scripts/` : データ検証・変換等の補助スクリプト

## セキュリティ

`.gitignore` により、認証情報、秘密鍵、`.env`、ローカル設定、一時ファイル等をコミット対象から除外します。
公開リポジトリのため、個人情報・認証情報・非公開資料は保存しません。

## Pilot 5自治体（2026-08-17）

広島市・庄原市・米子市・山田町・港区について、公式情報収集、Schema v1.0固定、一次QAまで完了しています。

- `data/master/01_municipalities_master.csv`: 143自治体の固定ID付きMASTER
- `data/research/pilot/`: municipality・categories・sourcesのPilotデータ
- `data/research/06_qa_log.csv`: Pilot QAログ
- `docs/schema/07_schema_v1.0.md`: Schema v1.0
- `docs/schema/08_data_dictionary_v1.0.md`: データ辞書
- `docs/schema/pilot_qa_report.md`: QA・RED TEAM結果
- `scripts/validate_pilot.py`: 件数・一意性・参照整合性検証

検証は `python3 scripts/validate_pilot.py` で実行できます。
