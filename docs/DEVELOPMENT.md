# 開発メモ

README から分けた、問題データの保守や開発向けの情報です。

## 目次

- [問題データの形式](#問題データの形式)
- [問題の追加と修正](#問題の追加と修正)
- [保守用スクリプトと未使用のファイル](#保守用スクリプトと未使用のファイル)
- [設定値](#設定値)
- [セッションに保存している値](#セッションに保存している値)
- [実装上の注意点](#実装上の注意点)
- [開発の経緯](#開発の経緯)

## 問題データの形式

`questions.json` は、次のような問題オブジェクトの配列です。

```json
{
  "id": 2,
  "category": "財務諸表分析",
  "difficulty": "中級",
  "question": "営業利益が黒字なのに営業CFがマイナス。最も疑うべきは？",
  "options": ["売掛金と在庫の急増", "減価償却費の増加", "支払利息の減少", "法人税の還付"],
  "answer": "売掛金と在庫の急増",
  "hint": "運転資本の変動を確認",
  "explanation": "利益とキャッシュは別物。運転資本増加はCFを圧迫する"
}
```

| キー | 必須 | 内容 |
| --- | :---: | --- |
| `id` | ○ | 整数。重複不可。Django 版では主キーになります |
| `category` | ○ | `財務諸表分析`・`ファンダメンタルズ`・`チャート分析` のいずれか |
| `difficulty` | ○ | `初級`・`中級`・`上級` のいずれか |
| `question` | ○ | 問題文 |
| `options` | ○ | 選択肢の配列（2 つ以上。現在のデータはすべて 4 つ） |
| `answer` | ○ | 正解。`options` のいずれかと完全に一致させます |
| `hint` | | ヒント |
| `explanation` | | 解説 |
| `chart_data` | | チャート用のデータ（現在のデータにはありません。下記参照） |
| `financial_data` | | 財務データの表（現在のデータにはありません。下記参照） |

- 必須キー・ID の重複・選択肢の数・正解が選択肢に含まれるかは、Streamlit 版の起動時（`load_questions`）と Django 版の取り込み時（`import_questions`）にチェックされます。
- `category` と `difficulty` の値はチェックされません。画面の選択肢は上の 3 種類ずつに固定されているため、ほかの値にすると「すべて」を選んだときにしか出題されません。
- `convert.py` で作ったデータでは、`options` の先頭が正解です。表示するときに問題ごとにシャッフルされます。

### 任意項目（chart_data / financial_data）の扱い

| 項目 | Streamlit 版 | Django 版 |
| --- | --- | --- |
| `chart_data` | `prices`（株価の配列）を折れ線、`volumes`（出来高の配列）を棒グラフで matplotlib により描画します。`hints` に `resistance`・`support` があれば、抵抗線・支持線を破線で表示します | `chart_data.image` があれば、その値を静的ファイルのパスとして画像を表示します。なければ「チャートデータあり（画像未設定）」と表示します |
| `financial_data` | pandas の表に変換し、「損益計算書」の見出しを付けて表示します | DB には保存されますが、画面には表示されません |

- Streamlit 版のチャートのフォントは Windows の日本語フォント（Meiryo UI など）を前提に指定されています。ほかの OS では、チャート内の日本語が正しく表示されない可能性があります。
- Django 版で `chart_data.image` の画像を表示するには、Django が静的ファイルとして見つけられる場所（例：`stock_quiz/quiz/static/` の下）に画像を置く必要があります。現在のリポジトリには、該当する画像も `STATICFILES_DIRS` の設定もありません。

## 問題の追加と修正

1. `questions.csv` を編集します。列は `id, category, difficulty, question, correct, wrong1, wrong2, wrong3, hint, explanation` です。
2. リポジトリ直下で変換します（pandas が必要です）。`questions.json` が上書きされます。

   ```bash
   python convert.py
   ```

3. Django 版の取り込み用ファイルにコピーします。

   ```powershell
   # Windows（PowerShell）
   Copy-Item questions.json stock_quiz\questions.json
   ```

   ```bash
   # macOS / Linux
   cp questions.json stock_quiz/questions.json
   ```

4. Django 版の DB に取り込みます。

   ```bash
   cd stock_quiz
   python manage.py import_questions
   ```

5. Streamlit 版は問題データを `st.cache_data` でキャッシュしているため、起動中のアプリには変更が反映されません。Streamlit を再起動してください。

注意点：

- CSV の `hint`・`explanation` が空欄だと、変換後のデータに文字列 `"nan"` が入ります（`convert.py` が欠損値を処理していないため）。空欄のまま変換しないでください。
- `import_questions` は ID ごとに追加・上書きするだけで、JSON から消した問題は DB から削除されません。不要になった問題は管理画面で削除してください。
- 管理画面で編集した問題は、同じ ID のまま `import_questions` を再実行すると、JSON の内容で上書きされます。
- 別の場所にある JSON は `python manage.py import_questions --path <JSON ファイルのパス>` で取り込めます。

## 保守用スクリプトと未使用のファイル

| ファイル | 内容 | 現在の状態と注意 |
| --- | --- | --- |
| `convert.py` | `questions.csv` を `questions.json` に変換します | 使用中。カレントディレクトリの `questions.json` を上書きします |
| `fix_chart_japanese_font.py` | `assets/` のチャート画像 6 枚を、日本語フォントを指定して再生成します（Windows は Meiryo など、macOS はヒラギノ、Linux は Noto Sans CJK などを探します） | `assets/` の PNG を上書きします。画像は現在のアプリでは使われていません |
| `apply_v2_1_patch.py` | 旧バージョン（v2.1）向けの修正です。チャート画像 6 枚の再生成と、`questions.json`・`app.py` の一部文言の置き換えを行います | 現在のデータとコードには置き換え対象がないため、実質的には画像の再生成だけです。ただし `questions.json` と `app.py` を書き直すので、実行する場合は差分を確認してください |
| `scripts/generate_charts.py` | 案内メッセージを表示するだけです | — |
| `utils/chart_generator.py` | `chart_data` から株価と出来高の 2 段チャートを作る関数です | 現在の `app.py` からは使われていません |
| `utils/score_manager.py` | 成績を `data/history.json` に追記する関数です | 使われていません |
| `assets/*.png` | ダブルボトム・ブレイクアウト・下降トレンドの、問題用と解答用のチャート画像（計 6 枚） | 旧バージョン（v2）で使用していました。現在は使われていません |
| `results.csv` | 旧バージョン（v2）の形式の成績履歴（日時・正答数・出題数・正答率・カテゴリ別・難易度別） | 現在のアプリは読み書きしません |

## 設定値

### Streamlit 版（`app.py` 冒頭）

| 定数 | 既定値 | 内容 |
| --- | --- | --- |
| `APP_VERSION` | `"2026-05-16_unbreakable_final"` | 画面上部に表示されるバージョン文字列 |
| `SHOW_HINT_DEFAULT` | `True` | 「ヒントを表示」の初期値 |
| `AUTO_ADVANCE` | `False` | 回答後に自動で次の問題へ進むかどうか |
| `AUTO_ADVANCE_SECONDS_CORRECT` / `AUTO_ADVANCE_SECONDS_WRONG` | `1.0` / `2.0` | 自動で進むまでの待ち時間（秒） |

`AUTO_ADVANCE` を `True` にすると、採点はされますが、正誤と解説が表示されないまま、待ち時間のあとに次の問題へ切り替わります（回答を処理する同じ実行の中で待機してから次の問題をセットするため）。

### Django 版

- `stock_quiz/quiz/views.py`：`SHOW_HINT_DEFAULT`（ヒント表示の初期値）、`CATEGORIES`・`DIFFICULTIES`（サイドバーの選択肢）
- `stock_quiz/stock_quiz/settings.py`：`LANGUAGE_CODE = 'ja'`、`TIME_ZONE = 'Asia/Tokyo'`、データベースは SQLite（`stock_quiz/db.sqlite3`）。`SECRET_KEY`・`DEBUG`・`ALLOWED_HOSTS` は開発用の値のままです（README の「本番環境で使うとき」を参照）

## セッションに保存している値

Django 版は次の値を `request.session` に保存します。Streamlit 版も、ほぼ同じ名前の値を `st.session_state` に持っています（加えて `current_q` と、ウィジェットのキーを切り替えるための `render_id`）。

| キー | 内容 |
| --- | --- |
| `current_qid` | 表示中の問題の ID |
| `queue_ids` | 出題待ちの問題 ID（シャッフル済み） |
| `filter_key` | `カテゴリ__難易度__件数` 形式のキー。変わるとキューを作り直します |
| `phase` | `question`（回答前）または `result`（回答後） |
| `fixed_options` / `fixed_qid` | 表示中の問題の、シャッフル済みの選択肢 |
| `last_result` / `last_answer` / `last_explanation` | 直前の回答の結果・正解・解説 |
| `score` | `{"correct": 正答数, "total": 出題数}` |
| `selected_cat` / `selected_diff` / `show_hint` | サイドバーの設定（Django 版のみ） |

## 実装上の注意点

- **取り込みは 1 問ずつ保存されます**：`import_questions` はトランザクションでまとめていないため、途中で不正なデータが見つかってエラー終了した場合、それより前の問題は取り込まれたままになります。
- **出題待ちキューと問題の削除**：キューは「件数」を含むキーで管理しているため、問題の追加・削除で件数が変われば作り直されます。ただし、削除と追加を同時に行って件数が変わらない場合は、削除済みの ID がキューに残り、その問題の番になると HTTP 500 エラーになります。「リセット（スコア＆出題順）」を押すと復旧します。
- **正解の色分け**：テンプレート内の `.opt-answer`（正解を緑色にするスタイル）は、詳細度の高い `.options label` のスタイルに上書きされて効いていません。
- **テンプレートの比較**：Django 版では、テンプレートに `==` による比較を書かず、ビューで計算したフラグ（`selected`・`is_answer`・`is_correct` など）を渡す方針です。

## 開発の経緯

コミット履歴から読み取れる流れです。

| 日付 | コミット | 内容 |
| --- | --- | --- |
| 2026-05-16 | `2abdcd4` | 最初の版（Streamlit）。24 問で、各問題が `title`・`point`・チャート画像（`assets/`）を持つ形式。成績を `results.csv` に記録。`tests/test_questions.py` もこのときのもの |
| 2026-05-16 | `a951ddf` | `app.py` を作り直し、`chart_data`（数値データ）から matplotlib でチャートを描く方式に変更。`questions.csv`・`convert.py`・`utils/` を追加し、カテゴリを現在の 3 種類に変更 |
| 2026-05-16 | `6296972` | README を更新 |
| 2026-05-20 | `63a5898` | 問題を 50 問に拡充（すべて文章題）。自動遷移を既定で無効に変更 |
| 2026-06-27 | `d3c07ee`・`1629e79`・`091f284` | Django へ移植（`stock_quiz/`）。`requirements.txt` を Django のみに変更し、`.gitignore` を追加 |
