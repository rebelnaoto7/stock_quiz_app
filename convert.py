import pandas as pd
import json

# CSV読み込み
df = pd.read_csv("questions.csv", encoding="utf-8")

questions = []

for _, row in df.iterrows():
    q = {
        "id": int(row["id"]),
        "category": str(row["category"]),
        "difficulty": str(row["difficulty"]),
        "question": str(row["question"]),
        "options": [
            str(row["correct"]),
            str(row["wrong1"]),
            str(row["wrong2"]),
            str(row["wrong3"])
        ],
        "answer": str(row["correct"]),
        "hint": str(row["hint"]) if "hint" in df.columns else "",
        "explanation": str(row["explanation"]) if "explanation" in df.columns else ""
    }

    questions.append(q)

# JSON書き出し
with open("questions.json", "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print(f"✅ questions.json 生成完了（{len(questions)}問）")