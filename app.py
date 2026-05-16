import json
import random
import time
from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib
import matplotlib.pyplot as plt


# =========================================================
# Config（必要ならここだけ触る）
# =========================================================
APP_VERSION = "2026-05-16_app_unbreakable_v1"
AUTO_ADVANCE = True
SLEEP_SEC_CORRECT = 0.8
SLEEP_SEC_WRONG = 1.6

# フォント（Windows想定）
matplotlib.rcParams["font.family"] = ["Meiryo UI", "Meiryo", "MS Gothic", "Yu Gothic", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False


# =========================================================
# Utils
# =========================================================
def rerun():
    """Streamlit version差異吸収"""
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()


def load_questions(path: str = "questions.json") -> list[dict]:
    p = Path(path)
    if not p.exists():
        st.error("questions.json が見つかりません。app.py と同じフォルダに置いてください。")
        st.stop()

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        st.error(f"questions.json が壊れています: {e}")
        st.stop()

    if not isinstance(data, list):
        st.error("questions.json は配列(list)である必要があります。")
        st.stop()

    required = {"id", "category", "difficulty", "question", "options", "answer"}
    ids = set()

    for i, q in enumerate(data):
        if not isinstance(q, dict):
            st.error(f"{i}番目の要素が dict ではありません。")
            st.stop()

        missing = required - set(q.keys())
        if missing:
            st.error(f"id={q.get('id')} の問題に必須キーが不足: {sorted(list(missing))}")
            st.stop()

        if q["id"] in ids:
            st.error(f"id が重複しています: {q['id']}")
            st.stop()
        ids.add(q["id"])

        if not isinstance(q["options"], list) or len(q["options"]) < 2:
            st.error(f"id={q['id']} の options は2つ以上の配列にしてください。")
            st.stop()

        if q["answer"] not in q["options"]:
            st.error(f"id={q['id']} の answer が options に含まれていません。")
            st.stop()

        # チャート分析は chart_data 必須（「チャートがない」事故を防ぐ）
        if q.get("category") == "チャート分析" and "chart_data" not in q:
            st.error(f"id={q['id']} はチャート分析ですが chart_data がありません。")
            st.stop()

    return data


def filter_questions(qs: list[dict], cat: str, diff: str) -> list[dict]:
    result = qs
    if cat != "すべて":
        result = [q for q in result if q.get("category") == cat]
    if diff != "すべて":
        result = [q for q in result if q.get("difficulty") == diff]
    # チャート分析は chart_data 無しなら除外（念のため）
    result = [q for q in result if q.get("category") != "チャート分析" or "chart_data" in q]
    return result


def render_chart(chart_data: dict):
    prices = chart_data.get("prices", [])
    volumes = chart_data.get("volumes", [])
    hints = chart_data.get("hints", {})  # {"resistance":..., "support":...}

    if not prices:
        st.warning("chart_data はありますが prices が空です。")
        return

    x = list(range(len(prices)))
    fig, ax1 = plt.subplots(figsize=(9, 4))

    ax1.plot(x, prices, linewidth=2, label="株価")
    ax1.grid(True, alpha=0.3)
    ax1.set_title("株価チャート")
    ax1.set_ylabel("株価")

    if isinstance(hints, dict):
        if "resistance" in hints:
            ax1.axhline(hints["resistance"], color="red", linestyle="--", alpha=0.7,
                        label=f"抵抗線 {hints['resistance']}")
        if "support" in hints:
            ax1.axhline(hints["support"], color="green", linestyle="--", alpha=0.7,
                        label=f"支持線 {hints['support']}")

    if volumes:
        ax2 = ax1.twinx()
        ax2.bar(x, volumes, alpha=0.25, label="出来高")
        ax2.set_ylabel("出来高")

    ax1.legend(loc="upper left")
    st.pyplot(fig, clear_figure=True)


# =========================================================
# Session State (一元管理)
# =========================================================
def ss_init():
    defaults = {
        "current_q": None,
        "answered": False,
        "score": {"correct": 0, "total": 0},
        "render_id": 0,

        # 出題キュー
        "queue_ids": [],
        "filter_key": "",

        # 選択肢固定（ここが「回答が動く」バグの解決点）
        "fixed_options": [],        # 現在問題の表示順
        "fixed_qid": None,          # fixed_options が紐づく問題id
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def make_filter_key(cat: str, diff: str, n: int) -> str:
    return f"{cat}__{diff}__{n}"


def rebuild_queue(filtered_list: list[dict]):
    ids = [q["id"] for q in filtered_list]
    random.shuffle(ids)
    st.session_state.queue_ids = ids


def set_current_question(q: dict):
    st.session_state.current_q = q
    st.session_state.answered = False
    st.session_state.render_id += 1

    # ✅ 選択肢は「このタイミングで1回だけ」シャッフルして固定
    opts = list(q["options"])
    random.shuffle(opts)
    st.session_state.fixed_options = opts
    st.session_state.fixed_qid = q["id"]


def pick_next_question(filtered_list: list[dict], cat: str, diff: str):
    if not filtered_list:
        st.session_state.current_q = None
        return

    fk = make_filter_key(cat, diff, len(filtered_list))
    if st.session_state.filter_key != fk:
        st.session_state.filter_key = fk
        rebuild_queue(filtered_list)

    if not st.session_state.queue_ids:
        rebuild_queue(filtered_list)

    next_id = st.session_state.queue_ids.pop(0)
    q = next(q for q in filtered_list if q["id"] == next_id)
    set_current_question(q)


# =========================================================
# App Main
# =========================================================
def main():
    st.set_page_config(page_title="株式投資マスタークイズ", page_icon="📊", layout="wide")
    st.caption(f"VERSION: {APP_VERSION}")

    ss_init()
    questions = load_questions("questions.json")

    # ----- Sidebar -----
    st.sidebar.title("⚙️ 設定")
    categories = ["すべて", "財務諸表分析", "ファンダメンタルズ", "チャート分析"]
    difficulties = ["すべて", "初級", "中級", "上級"]

    selected_cat = st.sidebar.selectbox("カテゴリ", categories, index=0)
    selected_diff = st.sidebar.selectbox("難易度", difficulties, index=0)
    show_hint = st.sidebar.checkbox("ヒントを表示", value=True)

    if st.sidebar.button("🔁 リセット（スコア＆出題順）", key="btn_reset_all"):
        st.session_state.score = {"correct": 0, "total": 0}
        st.session_state.current_q = None
        st.session_state.answered = False
        st.session_state.queue_ids = []
        st.session_state.filter_key = ""
        st.session_state.fixed_options = []
        st.session_state.fixed_qid = None
        st.session_state.render_id += 1
        rerun()

    filtered = filter_questions(questions, selected_cat, selected_diff)

    # ----- Header -----
    st.title("📊 株式投資マスタークイズ")

    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    col1.metric("正答数", st.session_state.score["correct"])
    col2.metric("出題数", st.session_state.score["total"])
    rate = (st.session_state.score["correct"] / st.session_state.score["total"] * 100) if st.session_state.score["total"] else 0
    col3.metric("正答率", f"{rate:.1f}%")
    col4.write(f"問題数: {len(filtered)}")

    if st.button("🎲 次の問題", key="btn_next_question"):
        pick_next_question(filtered, selected_cat, selected_diff)

    st.divider()

    # ----- Ensure current question -----
    if st.session_state.current_q is None and filtered:
        pick_next_question(filtered, selected_cat, selected_diff)

    q = st.session_state.current_q
    if not q:
        st.warning("表示できる問題がありません（フィルタ条件を変更してください）。")
        st.stop()

    qid = q["id"]
    rid = st.session_state.render_id

    # フィルタ変更等で current が範囲外になった場合
    if qid not in {qq["id"] for qq in filtered} and filtered:
        pick_next_question(filtered, selected_cat, selected_diff)
        q = st.session_state.current_q
        qid = q["id"]
        rid = st.session_state.render_id

    # ----- Question UI (ここ1箇所だけ) -----
    st.markdown(f"### Q. {q['question']}")
    st.caption(f"カテゴリ: {q.get('category','')} / 難易度: {q.get('difficulty','')}")

    if "financial_data" in q:
        st.markdown("### 📊 損益計算書")
        df = pd.DataFrame(q["financial_data"])
        st.dataframe(df, use_container_width=True)

    if "chart_data" in q:
        st.markdown("### 📈 チャート")
        render_chart(q["chart_data"])

    if show_hint and "hint" in q:
        with st.expander("💡 ヒント"):
            st.info(q["hint"])

    # ✅ 固定された選択肢（ここが重要：再描画で順番が変わらない）
    if st.session_state.fixed_qid != qid or not st.session_state.fixed_options:
        # 何らかの理由で未初期化なら補完
        opts = list(q["options"])
        random.shuffle(opts)
        st.session_state.fixed_options = opts
        st.session_state.fixed_qid = qid

    options = st.session_state.fixed_options

    # ----- Answer UI (フォームで固定：二重描画/キー衝突回避) -----
    form_key = f"form_{qid}_{rid}"
    radio_key = f"radio_{qid}_{rid}"

    with st.form(key=form_key):
        choice = st.radio("回答:", options, key=radio_key)
        submitted = st.form_submit_button("✅ 回答する")

    if submitted and not st.session_state.answered:
        st.session_state.answered = True
        st.session_state.score["total"] += 1

        correct = (choice == q["answer"])
        if correct:
            st.session_state.score["correct"] += 1
            st.success("✅ 正解")
        else:
            st.error(f"❌ 不正解（正解: {q['answer']}）")

        st.markdown("### 📝 解説")
        st.write(q.get("explanation", ""))

        if AUTO_ADVANCE:
            time.sleep(SLEEP_SEC_CORRECT if correct else SLEEP_SEC_WRONG)
            pick_next_question(filtered, selected_cat, selected_diff)
            rerun()


if __name__ == "__main__":
    main()