from pathlib import Path
import json

import matplotlib.pyplot as plt

# ============================================================
# Stock Quiz App v2.1 Patch
# 目的:
# - 問題出題時にも「抵抗線」「確認ライン」「底値圏」など、
#   チャート構造を理解するための情報を表示する
# - 解答後だけ「出来高確認」「即買いではなく反発確認」など、
#   判断プロセスを表示する
# ============================================================

plt.rcParams["font.family"] = "Meiryo UI"
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

LINE = "#2563eb"
GREEN = "#16a34a"
RED = "#dc2626"
ORANGE = "#f97316"
GRAY = "#64748b"
LIGHT_BG = "#f8fafc"
GRID = "#cbd5e1"
VOL = "#94a3b8"


def style_price_ax(ax, title):
    ax.set_title(title, fontsize=18, fontweight="bold", pad=16)
    ax.set_ylabel("株価", fontsize=12, fontweight="bold")
    ax.grid(True, color=GRID, linewidth=0.8, alpha=0.55)
    ax.set_facecolor(LIGHT_BG)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#334155")
    ax.spines["bottom"].set_color("#334155")
    ax.tick_params(axis="both", labelsize=10, colors="#0f172a")


def style_volume_ax(ax):
    ax.set_xlabel("時間", fontsize=12, fontweight="bold")
    ax.set_ylabel("出来高", fontsize=12, fontweight="bold")
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.35)
    ax.set_facecolor(LIGHT_BG)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#334155")
    ax.spines["bottom"].set_color("#334155")
    ax.tick_params(axis="both", labelsize=10, colors="#0f172a")


def annotate(ax, text, xy, xytext, color):
    ax.annotate(
        text,
        xy=xy,
        xytext=xytext,
        textcoords="data",
        fontsize=12,
        fontweight="bold",
        color=color,
        bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=color, lw=1.6),
        arrowprops=dict(arrowstyle="->", color=color, lw=2),
        ha="center",
        va="center",
    )


def save_price_volume_chart(filename, prices, volumes, title, answer_mode=False, chart_type="generic"):
    x = list(range(len(prices)))
    fig, (ax, axv) = plt.subplots(
        2,
        1,
        figsize=(11, 7.0),
        gridspec_kw={"height_ratios": [3.2, 1]},
        sharex=True,
    )

    line_color = RED if chart_type == "downtrend" else LINE
    ax.plot(x, prices, marker="o", markersize=6, linewidth=3, color=line_color)
    style_price_ax(ax, title)

    axv.bar(x, volumes, color=VOL, alpha=0.85)
    style_volume_ax(axv)

    # ============================================================
    # 問題出題時にも表示する情報
    # → チャート構造を理解するために必要な線・ラベル
    # ============================================================
    if chart_type == "double_bottom":
        ax.axhspan(80, 86, color="#dcfce7", alpha=0.55)
        ax.axhline(82, linestyle="--", linewidth=2, color=GREEN)
        ax.axhline(101, linestyle="--", linewidth=2, color=ORANGE)
        ax.text(0.2, 83, "底値圏", color=GREEN, fontsize=12, fontweight="bold", va="bottom")
        ax.text(8.7, 103, "確認ライン\n直近高値を超えるか", color=ORANGE, fontsize=11, fontweight="bold", ha="center")
        annotate(ax, "一番底", (7, 82), (5.7, 74), GREEN)
        annotate(ax, "二番底", (11, 84), (12.6, 76), GREEN)
        ax.set_ylim(72, 138)

    elif chart_type == "breakout":
        ax.axhline(90, linestyle="--", linewidth=2.5, color=ORANGE)
        ax.text(2, 91.5, "抵抗線", color=ORANGE, fontsize=12, fontweight="bold")
        ax.set_ylim(76, 118)

    elif chart_type == "downtrend":
        ax.plot([0, len(prices) - 1], [132, 82], linestyle="--", linewidth=2.5, color=GRAY)
        annotate(ax, "戻り高値を\n切り下げ", (2, 122), (3.3, 132), ORANGE)
        ax.set_ylim(76, 136)

    # ============================================================
    # 解答後だけ表示する情報
    # → 判断プロセス・行動判断に直結する注釈
    # ============================================================
    if answer_mode:
        if chart_type == "double_bottom":
            annotate(ax, "即買いではなく\n反発確認を待つ", (11, 84), (9.3, 116), RED)
            annotate(axv, "反発時の\n出来高確認", (13, volumes[13]), (10.6, max(volumes) * 0.8), ORANGE)

        elif chart_type == "breakout":
            ax.axvspan(10, 13.5, color="#dbeafe", alpha=0.75)
            annotate(ax, "抵抗線を上抜け", (10, 96), (8.5, 106), GREEN)
            annotate(ax, "出来高を伴うか\n確認する", (11, 102), (12.0, 88), RED)
            annotate(axv, "出来高増加", (10, volumes[10]), (7.8, max(volumes) * 0.8), GREEN)

        elif chart_type == "downtrend":
            ax.fill_between(x, prices, [min(prices) - 5] * len(prices), color="#fee2e2", alpha=0.5)
            annotate(ax, "下落継続", (8, 100), (9.5, 111), RED)
            annotate(ax, "買うなら\n転換確認後", (13, 82), (11.2, 92), GREEN)

    fig.tight_layout()
    fig.savefig(ASSETS / filename, dpi=180)
    plt.close(fig)


def regenerate_charts():
    save_price_volume_chart(
        "double_bottom_question.png",
        [100, 108, 116, 124, 132, 118, 96, 82, 92, 101, 93, 84, 86, 95, 108],
        [90, 100, 110, 120, 130, 160, 190, 240, 170, 150, 160, 220, 230, 260, 280],
        "二番底：底値圏と確認ラインを読む",
        answer_mode=False,
        chart_type="double_bottom",
    )

    save_price_volume_chart(
        "double_bottom_answer.png",
        [100, 108, 116, 124, 132, 118, 96, 82, 92, 101, 93, 84, 86, 95, 108],
        [90, 100, 110, 120, 130, 160, 190, 240, 170, 150, 160, 220, 230, 260, 280],
        "二番底：反発確認を待つ局面",
        answer_mode=True,
        chart_type="double_bottom",
    )

    save_price_volume_chart(
        "breakout_question.png",
        [80, 82, 81, 83, 84, 85, 84, 86, 88, 90, 96, 102, 108, 112],
        [80, 82, 76, 90, 88, 95, 92, 110, 120, 135, 260, 300, 280, 250],
        "高値ブレイク：抵抗線を読む",
        answer_mode=False,
        chart_type="breakout",
    )

    save_price_volume_chart(
        "breakout_answer.png",
        [80, 82, 81, 83, 84, 85, 84, 86, 88, 90, 96, 102, 108, 112],
        [80, 82, 76, 90, 88, 95, 92, 110, 120, 135, 260, 300, 280, 250],
        "高値ブレイク：出来高確認が重要",
        answer_mode=True,
        chart_type="breakout",
    )

    save_price_volume_chart(
        "downtrend_question.png",
        [130, 126, 122, 118, 115, 111, 108, 104, 100, 96, 92, 88, 85, 82],
        [150, 160, 170, 190, 210, 230, 250, 270, 290, 310, 330, 350, 360, 370],
        "下降トレンド：戻り高値の切り下げを読む",
        answer_mode=False,
        chart_type="downtrend",
    )

    save_price_volume_chart(
        "downtrend_answer.png",
        [130, 126, 122, 118, 115, 111, 108, 104, 100, 96, 92, 88, 85, 82],
        [150, 160, 170, 190, 210, 230, 250, 270, 290, 310, 330, 350, 360, 370],
        "下降トレンド：無計画な逆張りを避ける",
        answer_mode=True,
        chart_type="downtrend",
    )


def patch_questions_json():
    path = ROOT / "questions.json"
    if not path.exists():
        print("questions.json が見つかりません。チャートのみ再生成しました。")
        return

    questions = json.loads(path.read_text(encoding="utf-8"))

    for q in questions:
        if q.get("image") == "assets/double_bottom_question.png":
            q["answer_image_caption"] = "解答後チャート：構造情報に加えて、反発確認と出来高確認を表示"
            q["explanation"] = (
                "問題画面では底値圏、確認ライン、一番底、二番底を表示しています。"
                "これらは状況理解に必要な情報です。"
                "ただし、即買いではなく反発確認を待つという判断プロセスは解答後チャートで確認します。"
            )

        elif q.get("image") == "assets/breakout_question.png":
            q["question"] = q["question"].replace("株価が長く抑えられていた水準を上抜けました。", "株価が抵抗線を上抜けました。")
            q["question"] = q["question"].replace("株価も重要な水準を上抜けました。", "株価も抵抗線を上抜けました。")
            q["answer_image_caption"] = "解答後チャート：抵抗線に加えて、ブレイク位置と出来高確認を表示"
            q["explanation"] = (
                "問題画面では抵抗線を表示しています。"
                "抵抗線はブレイク問題を理解するために必要な構造情報です。"
                "解答後チャートでは、抵抗線を上抜けた位置と出来高確認の重要性を追加で確認します。"
            )

        elif q.get("image") == "assets/downtrend_question.png":
            q["answer_image_caption"] = "解答後チャート：戻り高値切り下げに加えて、下落継続と転換確認を表示"
            q["explanation"] = (
                "問題画面では下降トレンドラインと戻り高値の切り下げを表示しています。"
                "これはトレンド構造を理解するために必要です。"
                "解答後チャートでは、下落継続や転換確認の重要性を追加で確認します。"
            )

    path.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    print("questions.json を更新しました。")


def patch_app_caption():
    path = ROOT / "app.py"
    if not path.exists():
        print("app.py が見つかりません。")
        return

    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "問題用チャート：確認ライン・抵抗線などのヒントは非表示",
        "問題用チャート：構造理解に必要なラインは表示、判断プロセスは解答後に表示",
    )
    path.write_text(text, encoding="utf-8")
    print("app.py のチャートキャプションを更新しました。")


if __name__ == "__main__":
    regenerate_charts()
    patch_questions_json()
    patch_app_caption()
    print("v2.1修正が完了しました。")
