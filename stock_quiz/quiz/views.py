import random

from django.shortcuts import redirect, render

from .models import Question

# =========================
# CONFIG（Streamlit版の CONFIG を移植）
# =========================
SHOW_HINT_DEFAULT = True

CATEGORIES = ["すべて", "財務諸表分析", "ファンダメンタルズ", "チャート分析"]
DIFFICULTIES = ["すべて", "初級", "中級", "上級"]


# =========================
# SESSION STATE ヘルパ（st.session_state → request.session）
# =========================
def ss_defaults():
    return {
        "current_qid": None,
        "queue_ids": [],
        "filter_key": "",
        "phase": "question",
        "fixed_options": [],
        "fixed_qid": None,
        "last_result": None,
        "last_answer": None,
        "last_explanation": None,
        "score": {"correct": 0, "total": 0},
        "selected_cat": "すべて",
        "selected_diff": "すべて",
        "show_hint": SHOW_HINT_DEFAULT,
    }


def ss_init(session):
    for k, v in ss_defaults().items():
        if k not in session:
            session[k] = v


def ss_reset_result_state(session):
    session["phase"] = "question"
    session["last_result"] = None
    session["last_answer"] = None
    session["last_explanation"] = None


def ss_set_question(session, q: Question):
    session["current_qid"] = q.id
    ss_reset_result_state(session)
    opts = list(q.options)
    random.shuffle(opts)
    session["fixed_options"] = opts
    session["fixed_qid"] = q.id
    session.modified = True


# =========================
# QUIZ ENGINE
# =========================
def filtered_queryset(cat: str, diff: str):
    qs = Question.objects.all()
    if cat != "すべて":
        qs = qs.filter(category=cat)
    if diff != "すべて":
        qs = qs.filter(difficulty=diff)
    return qs


def make_filter_key(cat: str, diff: str, n: int) -> str:
    return f"{cat}__{diff}__{n}"


def rebuild_queue(session, ids):
    ids = list(ids)
    random.shuffle(ids)
    session["queue_ids"] = ids
    session.modified = True


def pick_next_question(session, cat: str, diff: str):
    ids = list(filtered_queryset(cat, diff).values_list("id", flat=True))
    if not ids:
        session["current_qid"] = None
        session.modified = True
        return

    fk = make_filter_key(cat, diff, len(ids))
    if session.get("filter_key") != fk:
        session["filter_key"] = fk
        rebuild_queue(session, ids)

    if not session.get("queue_ids"):
        rebuild_queue(session, ids)

    queue = session["queue_ids"]
    next_id = queue.pop(0)
    session["queue_ids"] = queue
    q = Question.objects.get(id=next_id)
    ss_set_question(session, q)


# =========================
# MAIN VIEW
# =========================
def quiz_view(request):
    session = request.session
    ss_init(session)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "filter":
            session["selected_cat"] = request.POST.get("category", "すべて")
            session["selected_diff"] = request.POST.get("difficulty", "すべて")
            session["show_hint"] = request.POST.get("show_hint") == "on"
            session["current_qid"] = None
            session["filter_key"] = ""
            session["queue_ids"] = []
            ss_reset_result_state(session)
            pick_next_question(session, session["selected_cat"], session["selected_diff"])
            session.modified = True
            return redirect("quiz")

        if action == "reset":
            for k, v in ss_defaults().items():
                if k in ("selected_cat", "selected_diff", "show_hint"):
                    continue
                session[k] = v
            session.modified = True
            return redirect("quiz")

        if action == "next":
            pick_next_question(session, session["selected_cat"], session["selected_diff"])
            return redirect("quiz")

        if action == "answer" and session.get("phase") == "question":
            qid = session.get("current_qid")
            choice = request.POST.get("choice")
            if qid is not None and choice is not None:
                q = Question.objects.get(id=qid)
                session["score"]["total"] += 1
                correct = choice == q.answer
                if correct:
                    session["score"]["correct"] += 1
                session["last_result"] = "correct" if correct else "wrong"
                session["last_answer"] = q.answer
                session["last_explanation"] = q.explanation
                session["phase"] = "result"
                session.modified = True
            return redirect("quiz")

    # ---- GET
    cat = session.get("selected_cat", "すべて")
    diff = session.get("selected_diff", "すべて")

    if session.get("current_qid") is None:
        pick_next_question(session, cat, diff)

    total_in_filter = filtered_queryset(cat, diff).count()

    q = None
    if session.get("current_qid") is not None:
        q = Question.objects.filter(id=session["current_qid"]).first()

    if q is not None and (session.get("fixed_qid") != q.id or not session.get("fixed_options")):
        opts = list(q.options)
        random.shuffle(opts)
        session["fixed_options"] = opts
        session["fixed_qid"] = q.id
        session.modified = True

    score = session["score"]
    rate = (score["correct"] / score["total"] * 100) if score["total"] else 0

    phase = session.get("phase", "question")
    last_answer = session.get("last_answer")
    last_result = session.get("last_result")
    raw_options = session.get("fixed_options", [])

    # ===== ここがポイント：比較(==)を全てPython側で済ませる =====
    # テンプレートには == を一切書かないことで、空白詰まり等の構文事故を根絶する。
    cat_options = [{"value": c, "selected": (c == cat)} for c in CATEGORIES]
    diff_options = [{"value": d, "selected": (d == diff)} for d in DIFFICULTIES]
    # 回答後の選択肢（どれが正解か）
    result_options = [{"text": o, "is_answer": (o == last_answer)} for o in raw_options]

    context = {
        "cat_options": cat_options,
        "diff_options": diff_options,
        "show_hint": session.get("show_hint", SHOW_HINT_DEFAULT),
        "q": q,
        "options": raw_options,            # 出題中（テキストのみ）
        "result_options": result_options,  # 回答後（正解フラグ付き）
        "is_question": (phase == "question"),
        "is_correct": (last_result == "correct"),
        "last_answer": last_answer,
        "last_explanation": session.get("last_explanation"),
        "score": score,
        "rate": rate,
        "total_in_filter": total_in_filter,
    }
    return render(request, "quiz/quiz.html", context)
