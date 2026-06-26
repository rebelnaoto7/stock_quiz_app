import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from quiz.models import Question


class Command(BaseCommand):
    """questions.json を Question テーブルに取り込む（Streamlit版 load_questions のバリデーションを移植）。

    使い方:
        python manage.py import_questions
        python manage.py import_questions --path C:\\path\\to\\questions.json
    """

    help = "questions.json を Question モデルに取り込みます（既存IDは更新）。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=None,
            help="questions.json のパス（省略時は BASE_DIR/questions.json）",
        )

    def handle(self, *args, **options):
        path = options["path"]
        json_path = Path(path) if path else Path(settings.BASE_DIR) / "questions.json"

        if not json_path.exists():
            raise CommandError(f"questions.json が見つかりません: {json_path}")

        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CommandError(f"questions.json が壊れています: {e}")

        if not isinstance(data, list):
            raise CommandError("questions.json は配列(list)である必要があります。")

        required = {"id", "category", "difficulty", "question", "options", "answer"}
        seen_ids = set()
        created, updated = 0, 0

        for i, q in enumerate(data):
            if not isinstance(q, dict):
                raise CommandError(f"{i}番目の要素が dict ではありません。")

            missing = required - set(q.keys())
            if missing:
                raise CommandError(f"id={q.get('id')} の問題に必須キーが不足: {sorted(missing)}")

            if q["id"] in seen_ids:
                raise CommandError(f"id が重複しています: {q['id']}")
            seen_ids.add(q["id"])

            if not isinstance(q["options"], list) or len(q["options"]) < 2:
                raise CommandError(f"id={q['id']} の options は2つ以上の配列にしてください。")

            if q["answer"] not in q["options"]:
                raise CommandError(f"id={q['id']} の answer が options に含まれていません。")

            obj, is_created = Question.objects.update_or_create(
                id=q["id"],
                defaults={
                    "category": q["category"],
                    "difficulty": q["difficulty"],
                    "question": q["question"],
                    "options": q["options"],
                    "answer": q["answer"],
                    "hint": q.get("hint", ""),
                    "explanation": q.get("explanation", ""),
                    "chart_data": q.get("chart_data"),
                    "financial_data": q.get("financial_data"),
                },
            )
            created += int(is_created)
            updated += int(not is_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"取り込み完了: 新規 {created} 件 / 更新 {updated} 件（合計 {len(data)} 問）"
            )
        )