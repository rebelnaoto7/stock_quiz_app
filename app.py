import csv
import json
import random
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

APP_TITLE = "株式投資クイズアプリ"
QUESTIONS_PATH = Path("questions.json")
RESULTS_PATH = Path("results.csv")

st.set_page_config(page_title=APP_TITLE, page_icon="📈", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] { font-family: "Meiryo UI", "Meiryo", sans-serif; }
.stApp { color: #f9fafb; }
.block-container { max-width: 1080px; padding-top: 2rem; }
.main-title { font-size: 34px; font-weight: 900; color: #f9fafb; margin-bottom: 6px; }
.sub-title { font-size: 17px; color: #d1d5db; margin-bottom: 20px; }
.meta-badge { display: inline-block; background-color: #1d4ed8; color: #ffffff; padding: 5px 12px; border-radius: 999px; font-size: 13px; font-weight: 800; margin-right: 8px; margin-bottom: 8px; }
.difficulty-badge { display: inline-block; background-color: #7c3aed; color: #ffffff; padding: 5px 12px; border-radius: 999px; font-size: 13px; font-weight: 800; margin-right: 8px; margin-bottom: 8px; }
.question-title { font-size: 25px; font-weight: 900; color: #ffffff; margin: 8px 0 14px 0; }
p, label, span, div { color: #f3f4f6; }
.stRadio label { color: #f3f4f6 !important; }
.result-card { padding: 16px; border-radius: 12px; margin: 14px 0 12px 0; line-height: 1.7; font-size: 16px; }
.result-correct { background-color: #064e3b; border-left: 6px solid #22c55e; }
.result-wrong { background-color: #4c1d1d; border-left: 6px solid #ef4444; }
.result-status { font-size: 18px; font-weight: 900; margin-bottom: 6px; }
.user-answer { color: #fde68a; font-weight: 900; }
.correct-answer { color: #bbf7d0; font-weight: 900; }
.explanation-card { background-color: #0f172a; color: #f9fafb; padding: 18px; border-radius: 14px; border: 1px solid #334155; border-left: 6px solid #60a5fa; margin: 14px 0 28px 0; line-height: 1.8; }
.explanation-title { font-size: 18px; font-weight: 900; color: #bfdbfe; margin-bottom: 10px; }
.explanation-section { background-color: #111827; padding: 12px 14px; border-radius: 10px; margin-top: 10px; }
.explanation-label { color: #93c5fd; font-weight: 900; margin-right: 6px; }
.explanation-point { color: #fde68a; font-weight: 900; }
.warning-box { background-color: #1f2937; color: #f9fafb; padding: 16px; border-radius: 12px; border-left: 5px solid #f97316; margin-top: 24px; line-height: 1.7; }
[data-testid="stImageCaption"] { color: #d1d5db; font-size: 14px; }
</style>
""", unsafe_allow_html=True)


def load_questions(path: Path = QUESTIONS_PATH) -> list[dict]:
    if not path.exists():
        st.error(f"{path} が見つかりません。")
        st.stop()
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def initialize_state():
    defaults = {
        "quiz_started": False,
        "quiz_finished": False,
        "quiz_questions": [],
        "current_index": 0,
        "answers": {},
        "submitted_current": False,
        "last_saved": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def filter_questions(questions, categories, difficulties):
    return [
        q for q in questions
        if q.get("category") in categories and q.get("difficulty") in difficulties
    ]


def start_quiz(selected_questions):
    st.session_state.quiz_questions = selected_questions
    st.session_state.current_index = 0
    st.session_state.answers = {}
    st.session_state.quiz_started = True
    st.session_state.quiz_finished = False
    st.session_state.submitted_current = False
    st.session_state.last_saved = False


def calculate_results(quiz_questions, answers):
    total = len(quiz_questions)
    correct = 0
    by_category = {}
    by_difficulty = {}
    for q in quiz_questions:
        qid = str(q["id"])
        is_correct = answers.get(qid) == q["answer"]
        if is_correct:
            correct += 1
        category = q.get("category", "未分類")
        difficulty = q.get("difficulty", "未設定")
        by_category.setdefault(category, {"correct": 0, "total": 0})
        by_difficulty.setdefault(difficulty, {"correct": 0, "total": 0})
        by_category[category]["total"] += 1
        by_difficulty[difficulty]["total"] += 1
        if is_correct:
            by_category[category]["correct"] += 1
            by_difficulty[difficulty]["correct"] += 1
    accuracy = correct / total if total else 0
    return correct, total, accuracy, by_category, by_difficulty


def save_history(correct, total, accuracy, by_category, by_difficulty):
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    file_exists = RESULTS_PATH.exists()
    row = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": correct,
        "total": total,
        "accuracy": round(accuracy, 4),
        "category_scores": json.dumps(by_category, ensure_ascii=False),
        "difficulty_scores": json.dumps(by_difficulty, ensure_ascii=False),
    }
    with RESULTS_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def show_question(q):
    st.progress((st.session_state.current_index + 1) / len(st.session_state.quiz_questions))
    st.write(f"進捗：{st.session_state.current_index + 1} / {len(st.session_state.quiz_questions)} 問")
    st.markdown(f'<span class="meta-badge">{q.get("category", "総合")}</span><span class="difficulty-badge">{q.get("difficulty", "未設定")}</span>', unsafe_allow_html=True)
    st.markdown(f'<div class="question-title">{q["title"]}</div>', unsafe_allow_html=True)
    st.write(q["question"])

    image_path = q.get("image")
    if image_path and Path(image_path).exists():
        st.image(image_path, caption="問題用チャート：構造理解に必要なラインは表示、判断プロセスは解答後に表示", use_container_width=True)

    key = f"answer_{q['id']}"
    selected = st.radio(
        "選択肢を選んでください",
        options=list(q["options"].keys()),
        format_func=lambda x: f"{x}. {q['options'][x]}",
        key=key,
        disabled=st.session_state.submitted_current,
    )

    if not st.session_state.submitted_current:
        if st.button("回答する", type="primary"):
            st.session_state.answers[str(q["id"])] = selected
            st.session_state.submitted_current = True
            st.rerun()

    if st.session_state.submitted_current:
        show_answer(q)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("次の問題へ"):
                if st.session_state.current_index + 1 >= len(st.session_state.quiz_questions):
                    st.session_state.quiz_finished = True
                else:
                    st.session_state.current_index += 1
                    st.session_state.submitted_current = False
                st.rerun()
        with col2:
            if st.button("最初からやり直す"):
                reset_quiz()
                st.rerun()


def show_answer(q):
    user_answer = st.session_state.answers.get(str(q["id"]))
    correct_answer = q["answer"]
    is_correct = user_answer == correct_answer
    card_class = "result-card result-correct" if is_correct else "result-card result-wrong"
    status_text = "正解：あなたの回答は正解です" if is_correct else "不正解：あなたの回答は不正解です"

    st.markdown(f"""
    <div class="{card_class}">
        <div class="result-status">{q["title"]}：{status_text}</div>
        <div><strong>あなたの回答：</strong><span class="user-answer">{user_answer}. {q["options"][user_answer]}</span></div>
        <div><strong>正解：</strong><span class="correct-answer">{correct_answer}. {q["options"][correct_answer]}</span></div>
    </div>
    """, unsafe_allow_html=True)

    answer_image = q.get("answer_image")
    if answer_image and Path(answer_image).exists():
        st.markdown("#### 解答後のチャート解説")
        st.image(answer_image, caption=q.get("answer_image_caption", "解答後チャート"), use_container_width=True)

    st.markdown(f"""
    <div class="explanation-card">
        <div class="explanation-title">解説</div>
        <div class="explanation-section"><span class="explanation-label">分類：</span>{q.get("category", "総合")}</div>
        <div class="explanation-section"><span class="explanation-label">難易度：</span>{q.get("difficulty", "未設定")}</div>
        <div class="explanation-section"><span class="explanation-label">判断ポイント：</span><span class="explanation-point">{q.get("point", "")}</span></div>
        <div class="explanation-section"><span class="explanation-label">理由：</span>{q["explanation"]}</div>
    </div>
    """, unsafe_allow_html=True)


def reset_quiz():
    st.session_state.quiz_started = False
    st.session_state.quiz_finished = False
    st.session_state.quiz_questions = []
    st.session_state.current_index = 0
    st.session_state.answers = {}
    st.session_state.submitted_current = False
    st.session_state.last_saved = False


def show_history():
    st.sidebar.divider()
    st.sidebar.subheader("学習履歴")
    if RESULTS_PATH.exists():
        df = pd.read_csv(RESULTS_PATH)
        st.sidebar.write(f"履歴件数：{len(df)}")
        latest = df.tail(5)[["datetime", "score", "total", "accuracy"]]
        st.sidebar.dataframe(latest, use_container_width=True)
    else:
        st.sidebar.caption("履歴はまだありません。")


def show_summary():
    correct, total, accuracy, by_category, by_difficulty = calculate_results(st.session_state.quiz_questions, st.session_state.answers)
    if not st.session_state.last_saved:
        save_history(correct, total, accuracy, by_category, by_difficulty)
        st.session_state.last_saved = True

    st.subheader("最終結果")
    st.metric("総合正解数", f"{correct} / {total}")
    st.progress(accuracy)
    st.write(f"正答率：{accuracy:.1%}")

    st.subheader("分類別スコア")
    st.dataframe(pd.DataFrame([
        {"分類": k, "正解数": v["correct"], "問題数": v["total"], "正答率": f"{v['correct'] / v['total']:.1%}"}
        for k, v in by_category.items()
    ]), use_container_width=True)

    st.subheader("難易度別スコア")
    st.dataframe(pd.DataFrame([
        {"難易度": k, "正解数": v["correct"], "問題数": v["total"], "正答率": f"{v['correct'] / v['total']:.1%}"}
        for k, v in by_difficulty.items()
    ]), use_container_width=True)

    if st.button("新しいクイズを開始"):
        reset_quiz()
        st.rerun()


# Main
initialize_state()
all_questions = load_questions()
st.markdown('<div class="main-title">📈 株式投資クイズアプリ</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">チャート分析・ファンダメンタルズ・総合判断を1問ずつ学習できます。</div>', unsafe_allow_html=True)

categories = sorted({q.get("category", "未分類") for q in all_questions})
difficulties = ["初級", "中級", "上級"]

st.sidebar.header("出題設定")
selected_categories = st.sidebar.multiselect("カテゴリ", categories, default=categories)
selected_difficulties = st.sidebar.multiselect("難易度", difficulties, default=difficulties)
mode = st.sidebar.selectbox("出題モード", ["ランダム出題", "順番に出題"])
filtered = filter_questions(all_questions, selected_categories, selected_difficulties)
max_questions = max(1, len(filtered)) if filtered else 1
num_questions = st.sidebar.slider("出題数", 1, max_questions, min(5, max_questions))
show_history()

if not filtered:
    st.warning("条件に一致する問題がありません。カテゴリまたは難易度を変更してください。")
    st.stop()

if not st.session_state.quiz_started:
    st.info("左の設定を確認して、クイズを開始してください。")
    if st.button("クイズを開始", type="primary"):
        selected = filtered.copy()
        if mode == "ランダム出題":
            random.shuffle(selected)
        selected = selected[:num_questions]
        start_quiz(selected)
        st.rerun()
elif st.session_state.quiz_finished:
    show_summary()
else:
    current_question = st.session_state.quiz_questions[st.session_state.current_index]
    show_question(current_question)

st.markdown("""
<div class="warning-box">
<strong>注意：</strong><br>
このアプリは投資学習用です。特定銘柄の売買を推奨するものではありません。
実際の投資判断では、業績、財務状況、バリュエーション、市場環境、リスク許容度を総合的に確認してください。
</div>
""", unsafe_allow_html=True)
