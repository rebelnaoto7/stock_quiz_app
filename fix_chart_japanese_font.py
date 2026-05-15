from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)


def get_japanese_font():
    candidates = [
        Path(r"C:\Windows\Fonts\meiryo.ttc"),
        Path(r"C:\Windows\Fonts\meiryob.ttc"),
        Path(r"C:\Windows\Fonts\YuGothM.ttc"),
        Path(r"C:\Windows\Fonts\YuGothR.ttc"),
        Path(r"C:\Windows\Fonts\msgothic.ttc"),
        Path("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
    ]
    for p in candidates:
        if p.exists():
            return fm.FontProperties(fname=str(p))
    return fm.FontProperties(family="sans-serif")

JP_FONT = get_japanese_font()
plt.rcParams["axes.unicode_minus"] = False

LINE = "#2563eb"
GREEN = "#16a34a"
RED = "#dc2626"
ORANGE = "#f97316"
GRAY = "#64748b"
LIGHT_BG = "#f8fafc"
GRID = "#cbd5e1"
VOL = "#94a3b8"


def jp_text(ax, x, y, text, **kwargs):
    kwargs.setdefault("fontproperties", JP_FONT)
    return ax.text(x, y, text, **kwargs)


def style_price_ax(ax, title):
    ax.set_title(title, fontsize=18, fontweight="bold", pad=16, fontproperties=JP_FONT)
    ax.set_ylabel("株価", fontsize=12, fontweight="bold", fontproperties=JP_FONT)
    ax.grid(True, color=GRID, linewidth=0.8, alpha=0.55)
    ax.set_facecolor(LIGHT_BG)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", labelsize=10, colors="#0f172a")


def style_volume_ax(ax):
    ax.set_xlabel("時間", fontsize=12, fontweight="bold", fontproperties=JP_FONT)
    ax.set_ylabel("出来高", fontsize=12, fontweight="bold", fontproperties=JP_FONT)
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.35)
    ax.set_facecolor(LIGHT_BG)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
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
        fontproperties=JP_FONT,
        bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=color, lw=1.6),
        arrowprops=dict(arrowstyle="->", color=color, lw=2),
        ha="center",
        va="center",
    )


def save_price_volume_chart(filename, prices, volumes, title, answer_mode=False, chart_type="generic"):
    x = list(range(len(prices)))
    fig, (ax, axv) = plt.subplots(2, 1, figsize=(11, 7.0), gridspec_kw={"height_ratios": [3.2, 1]}, sharex=True)
    line_color = RED if chart_type == "downtrend" else LINE
    ax.plot(x, prices, marker="o", markersize=6, linewidth=3, color=line_color)
    style_price_ax(ax, title)
    axv.bar(x, volumes, color=VOL, alpha=0.85)
    style_volume_ax(axv)

    # 問題出題時にも表示する構造情報
    if chart_type == "double_bottom":
        ax.axhspan(80, 86, color="#dcfce7", alpha=0.55)
        ax.axhline(82, linestyle="--", linewidth=2, color=GREEN)
        ax.axhline(101, linestyle="--", linewidth=2, color=ORANGE)
        jp_text(ax, 0.2, 83, "底値圏", color=GREEN, fontsize=12, fontweight="bold", va="bottom")
        jp_text(ax, 8.7, 103, "確認ライン\n直近高値を超えるか", color=ORANGE, fontsize=11, fontweight="bold", ha="center")
        annotate(ax, "一番底", (7, 82), (5.7, 74), GREEN)
        annotate(ax, "二番底", (11, 84), (12.6, 76), GREEN)
        ax.set_ylim(72, 138)
    elif chart_type == "breakout":
        ax.axhline(90, linestyle="--", linewidth=2.5, color=ORANGE)
        jp_text(ax, 2, 91.5, "抵抗線", color=ORANGE, fontsize=12, fontweight="bold")
        ax.set_ylim(76, 118)
    elif chart_type == "downtrend":
        ax.plot([0, len(prices)-1], [132, 82], linestyle="--", linewidth=2.5, color=GRAY)
        annotate(ax, "戻り高値を\n切り下げ", (2, 122), (3.3, 132), ORANGE)
        ax.set_ylim(76, 136)

    # 解答後だけ表示する判断プロセス
    if answer_mode:
        if chart_type == "double_bottom":
            annotate(ax, "即買いではなく\n反発確認を待つ", (11, 84), (9.3, 116), RED)
            annotate(axv, "反発時の\n出来高確認", (13, volumes[13]), (10.6, max(volumes)*0.8), ORANGE)
        elif chart_type == "breakout":
            ax.axvspan(10, 13.5, color="#dbeafe", alpha=0.75)
            annotate(ax, "抵抗線を上抜け", (10, 96), (8.5, 106), GREEN)
            annotate(ax, "出来高を伴うか\n確認する", (11, 102), (12.0, 88), RED)
            annotate(axv, "出来高増加", (10, volumes[10]), (7.8, max(volumes)*0.8), GREEN)
        elif chart_type == "downtrend":
            ax.fill_between(x, prices, [min(prices)-5]*len(prices), color="#fee2e2", alpha=0.5)
            annotate(ax, "下落継続", (8, 100), (9.5, 111), RED)
            annotate(ax, "買うなら\n転換確認後", (13, 82), (11.2, 92), GREEN)

    fig.tight_layout()
    fig.savefig(ASSETS / filename, dpi=180)
    plt.close(fig)


def regenerate_charts():
    save_price_volume_chart("double_bottom_question.png", [100,108,116,124,132,118,96,82,92,101,93,84,86,95,108], [90,100,110,120,130,160,190,240,170,150,160,220,230,260,280], "二番底：底値圏と確認ラインを読む", False, "double_bottom")
    save_price_volume_chart("double_bottom_answer.png", [100,108,116,124,132,118,96,82,92,101,93,84,86,95,108], [90,100,110,120,130,160,190,240,170,150,160,220,230,260,280], "二番底：反発確認を待つ局面", True, "double_bottom")
    save_price_volume_chart("breakout_question.png", [80,82,81,83,84,85,84,86,88,90,96,102,108,112], [80,82,76,90,88,95,92,110,120,135,260,300,280,250], "高値ブレイク：抵抗線を読む", False, "breakout")
    save_price_volume_chart("breakout_answer.png", [80,82,81,83,84,85,84,86,88,90,96,102,108,112], [80,82,76,90,88,95,92,110,120,135,260,300,280,250], "高値ブレイク：出来高確認が重要", True, "breakout")
    save_price_volume_chart("downtrend_question.png", [130,126,122,118,115,111,108,104,100,96,92,88,85,82], [150,160,170,190,210,230,250,270,290,310,330,350,360,370], "下降トレンド：戻り高値の切り下げを読む", False, "downtrend")
    save_price_volume_chart("downtrend_answer.png", [130,126,122,118,115,111,108,104,100,96,92,88,85,82], [150,160,170,190,210,230,250,270,290,310,330,350,360,370], "下降トレンド：無計画な逆張りを避ける", True, "downtrend")


if __name__ == "__main__":
    regenerate_charts()
    print("日本語フォント修正版チャートを再生成しました。")
    font_file = JP_FONT.get_file()
    print(f"使用フォント: {font_file if font_file else JP_FONT.get_name()}")
