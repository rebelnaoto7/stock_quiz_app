# Stock Investment Quiz App v2

チャート分析とファンダメンタルズを組み合わせて、株式投資の判断力を鍛える Streamlit アプリです。

## v2で追加した8つの改善

1. 難易度分類を追加
2. 問題をランダム出題に対応
3. 正答率・履歴を `results.csv` に保存
4. 出来高付きチャートに変更
5. 問題数を24問に拡張
6. UIを1問ずつ表示する形式に変更
7. Streamlit Community Cloud でデプロイしやすい構成に整理
8. `pytest` 用のテストコードを追加

## ファイル構成

```text
stock_quiz_app/
├─ app.py
├─ questions.json
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ .streamlit/
│  └─ config.toml
├─ assets/
│  ├─ double_bottom_question.png
│  ├─ double_bottom_answer.png
│  ├─ breakout_question.png
│  ├─ breakout_answer.png
│  ├─ downtrend_question.png
│  └─ downtrend_answer.png
├─ scripts/
│  └─ generate_charts.py
└─ tests/
   └─ test_questions.py
```

## セットアップ

```powershell
python -m venv .venv
.venv\Scriptsctivate
pip install -r requirements.txt
streamlit run app.py
```

## テスト実行

```powershell
pytest
```

## デプロイ

Streamlit Community Cloud にデプロイする場合は、GitHubにこのリポジトリをPushし、メインファイルとして `app.py` を指定します。

## 注意事項

このアプリは投資学習を目的としたものです。特定銘柄の売買を推奨するものではありません。
