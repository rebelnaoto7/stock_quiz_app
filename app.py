import json
import random
from pathlib import Path

import pandas as pd
import streamlit as st
import matplotlib
import matplotlib.pyplot as plt

# =========================
# CONFIG（ここだけ触れば挙動が変わる）
# =========================
APP_VERSION = "2026-05-16_unbreakable_final"
SHOW_HINT_DEFAULT = True

# 自動遷移は「学習用途では事故りやすい」のでデフォルトOFF
AUTO_ADVANCE = False
AUTO_ADVANCE_SECONDS_CORRECT = 1.0
AUTO_ADVANCE_SECONDS_WRONG = 2.0

# フォント（Windows想定）
matplotlib.rcParams["font.family"] = ["Meiryo UI", "Meiryo", "MS Gothic", "Yu Gothic", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False


# =========================
# SAFE RERUN（Streamlit差異吸収）
# =========================
def safe_rerun():
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()


# =========================
# SESSION STATE（最重要：ここで全状態を一元定義）
# =========================
def ss_init():
    defaults = {
        # 現在の問題
        "current_q": None,
        "current_qid": None,

        # 出題順（重複しない）
        "queue_ids": [],
        "filter_key": "",

        # UIフェーズ（ここが「回答前に正解表示」の完全対策）
        # "question" = 回答前、"result" = 回答後
        "phase": "question",

        # 選択肢を固定（「選んだのに動く」対策）
        "fixed_options": [],
        "fixed_qid": None,

        # 回答結果の保持（次の問題に持ち越さない）
        "last_result": None,         # "correct" / "wrong"
        "last_answer": None,
        "last_explanation": None,

        # スコア
        "score": {"correct": 0, "total": 0},

        # UI key 衝突回避
        "render_id": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def ss_reset_result_state():
    """次の問題に移るときに必ず呼ぶ（持ち越し事故を0にする）"""
    st.session_state.phase = "question"
    st.session_state.last_result = None
    st.session_state.last_answer = None
    st.session_state.last_explanation = None


def ss_set_question(q: dict):
    """問題をセットするときの唯一の入口（ここで全て初期化・固定化する）"""
    st.session_state.current_q = q
    st.session_state.current_qid = q["id"]
    st.session_state.render_id += 1

    # 次の問題になったら結果系は必ず消す
    ss_reset_result_state()

    # 選択肢は「この瞬間に1回だけ」シャッフルして固定
    opts = list(q["options"])
    random.shuffle(opts)
    st.session_state.fixed_options = opts
    st.session_state.fixed_qid = q["id"]


# =========================
# DATA LOAD / VALIDATION
# =========================
@st.cache_data
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

        # チャート分析でも chart_data が無い場合は「止めない」（CSV運用想定）
        # 表示側で chart_data があれば描画する

    return data


def filter_questions(qs: list[dict], cat: str, diff: str) -> list[dict]:
    result = qs
    if cat != "すべて":
        result = [q for q in result if q.get("category") == cat]
    if diff != "すべて":
        result = [q for q in result if q.get("difficulty") == diff]
    return result


# =========================
# CHART RENDER
# =========================
def render_chart(chart_data: dict):
    prices = chart_data.get("prices", [])
    volumes = chart_data.get("volumes", [])
    hints = chart_data.get("hints", {})  # {"resistance":..., "support":...}

    if not prices:
        st.info("チャートデータがありません（prices が空）。")
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


# =========================
# QUIZ ENGINE（重複しない出題）
# =========================
def make_filter_key(cat: str, diff: str, n: int) -> str:
    return f"{cat}__{diff}__{n}"


def rebuild_queue(filtered_list: list[dict]):
    ids = [q["id"] for q in filtered_list]
    random.shuffle(ids)
    st.session_state.queue_ids = ids


def pick_next_question(filtered_list: list[dict], cat: str, diff: str):
    if not filtered_list:
        st.session_state.current_q = None
        st.session_state.current_qid = None
        return

    fk = make_filter_key(cat, diff, len(filtered_list))
    if st.session_state.filter_key != fk:
        st.session_state.filter_key = fk
        rebuild_queue(filtered_list)

    if not st.session_state.queue_ids:
        rebuild_queue(filtered_list)

    next_id = st.session_state.queue_ids.pop(0)
    q = next(q for q in filtered_list if q["id"] == next_id)
    ss_set_question(q)


# =========================
# MAIN
# =========================
def main():
    st.set_page_config(page_title="株式投資マスタークイズ", page_icon="📊", layout="wide")
    st.caption(f"VERSION: {APP_VERSION}")

    ss_init()
    questions = load_questions("questions.json")

    # ---- Sidebar
    st.sidebar.title("⚙️ 設定")
    categories = ["すべて", "財務諸表分析", "ファンダメンタルズ", "チャート分析"]
    difficulties = ["すべて", "初級", "中級", "上級"]

    selected_cat = st.sidebar.selectbox("カテゴリ", categories, index=0)
    selected_diff = st.sidebar.selectbox("難易度", difficulties, index=0)
    show_hint = st.sidebar.checkbox("ヒントを表示", value=SHOW_HINT_DEFAULT)

    if st.sidebar.button("🔁 リセット（スコア＆出題順）", key="btn_reset_all"):
        st.session_state.score = {"correct": 0, "total": 0}
        st.session_state.queue_ids = []
        st.session_state.filter_key = ""
        st.session_state.current_q = None
        st.session_state.current_qid = None
        st.session_state.fixed_options = []
        st.session_state.fixed_qid = None
        ss_reset_result_state()
        st.session_state.render_id += 1
        safe_rerun()

    # ---- Filter
    filtered = filter_questions(questions, selected_cat, selected_diff)

    # ---- Header
    st.title("📊 株式投資マスタークイズ")

    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    col1.metric("正答数", st.session_state.score["correct"])
    col2.metric("出題数", st.session_state.score["total"])
    rate = (st.session_state.score["correct"] / st.session_state.score["total"] * 100) if st.session_state.score["total"] else 0
    col3.metric("正答率", f"{rate:.1f}%")
    col4.write(f"問題数: {len(filtered)}")

    # 次の問題（いつでも押せるが、押した瞬間に結果はリセットされる）
    if st.button("🎲 次の問題", key="btn_next_question"):
        pick_next_question(filtered, selected_cat, selected_diff)

    st.divider()

    # ---- Ensure current question
    if st.session_state.current_q is None and filtered:
        pick_next_question(filtered, selected_cat, selected_diff)

    q = st.session_state.current_q
    if not q:
        st.warning("表示できる問題がありません（フィルタ条件を変更してください）。")
        st.stop()

    qid = q["id"]
    rid = st.session_state.render_id

    # ---- Question
    st.markdown(f"### Q. {q['question']}")
    st.caption(f"カテゴリ: {q.get('category','')} / 難易度: {q.get('difficulty','')}")

    # 財務データ
    if "financial_data" in q:
        st.markdown("### 📊 損益計算書")
        df = pd.DataFrame(q["financial_data"])
        st.dataframe(df, use_container_width=True)

    # チャート（あれば）
    if "chart_data" in q:
        st.markdown("### 📈 チャート")
        render_chart(q["chart_data"])

    # ヒント
    if show_hint and "hint" in q and q.get("hint"):
        with st.expander("💡 ヒント"):
            st.info(q["hint"])

    # ---- Options (fixed)
    # 何らかの理由で固定選択肢が未設定なら補完
    if st.session_state.fixed_qid != qid or not st.session_state.fixed_options:
        opts = list(q["options"])
        random.shuffle(opts)
        st.session_state.fixed_options = opts
        st.session_state.fixed_qid = qid

    options = st.session_state.fixed_options

    # ---- Answer form
    form_key = f"form_{qid}_{rid}"
    radio_key = f"radio_{qid}_{rid}"

    with st.form(key=form_key):
        choice = st.radio("回答:", options, key=radio_key)
        submitted = st.form_submit_button("✅ 回答する")

    # ---- Grading (only once)
    if submitted and st.session_state.phase == "question":
        st.session_state.score["total"] += 1
        correct = (choice == q["answer"])
        if correct:
            st.session_state.score["correct"] += 1

        st.session_state.last_result = "correct" if correct else "wrong"
        st.session_state.last_answer = q["answer"]
        st.session_state.last_explanation = q.get("explanation", "")
        st.session_state.phase = "result"

        # 自動遷移（任意）
        if AUTO_ADVANCE:
            import time
            time.sleep(AUTO_ADVANCE_SECONDS_CORRECT if correct else AUTO_ADVANCE_SECONDS_WRONG)
            pick_next_question(filtered, selected_cat, selected_diff)
            safe_rerun()
        else:
            safe_rerun()

    # ---- Result UI (phase=="result" のときだけ出す → 回答前に出ない)
    if st.session_state.phase == "result":
        if st.session_state.last_result == "correct":
            st.success("✅ 正解")
        elif st.session_state.last_result == "wrong":
            st.error(f"❌ 不正解（正解: {st.session_state.last_answer}）")

        if st.session_state.last_explanation:
            st.markdown("### 📝 解説")
            st.write(st.session_state.last_explanation)

        # 次へ（回答後のみ表示）
        if st.button("➡ 次の問題へ", key=f"btn_next_after_{qid}_{rid}"):
            pick_next_question(filtered, selected_cat, selected_diff)
            safe_rerun()


if __name__ == "__main__":
    main()