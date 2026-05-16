import matplotlib.pyplot as plt
import numpy as np

def generate_chart(chart_data):
    """chart_data: dict with keys: prices, volumes, hints(optional)"""
    prices = chart_data["prices"]
    volumes = chart_data.get("volumes", [])
    hints = chart_data.get("hints", {})  # {"resistance": 1200, "support": 900}

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 6),
        gridspec_kw={"height_ratios": [3, 1]}, sharex=True
    )

    x = np.arange(len(prices))
    ax1.plot(x, prices, color="#1f77b4", linewidth=2, label="株価")
    ax1.fill_between(x, prices, min(prices), alpha=0.1, color="#1f77b4")

    # 抵抗線・支持線
    if "resistance" in hints:
        ax1.axhline(hints["resistance"], color="red", linestyle="--", alpha=0.7, label=f"抵抗線 {hints['resistance']}")
    if "support" in hints:
        ax1.axhline(hints["support"], color="green", linestyle="--", alpha=0.7, label=f"支持線 {hints['support']}")

    ax1.set_ylabel("株価（円）")
    ax1.legend(loc="upper left")
    ax1.grid(alpha=0.3)
    ax1.set_title("株価チャート")

    # 出来高
    if volumes:
        ax2.bar(x, volumes, color="#888", alpha=0.6)
        ax2.set_ylabel("出来高")
        ax2.set_xlabel("日数")
        ax2.grid(alpha=0.3)

    plt.tight_layout()
    return fig