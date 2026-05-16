import pandas as pd
import json

df = pd.read_csv("questions.csv")

questions = []

for _, row in df.iterrows():
    q = {
        "id": int(row["id"]),
        "category": row["category"],
        "difficulty": row["difficulty"],
        "title": row["title"],
        "question": row["question"],
        "options": {
            "A": row["option_A"],
            "B": row["option_B"],
            "C": row["option_C"],
            "D": row["option_D"]
        },
        "answer": row["answer"],
        "point": row["point"],
        "explanation": row["explanation"],
        "image": None if pd.isna(row.get("image")) else row["image"],
        "answer_image": None if pd.isna(row.get("answer_image")) else row["answer_image"]
    }

    questions.append(q)

with open("questions.json", "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print("✅ JSON生成完了")