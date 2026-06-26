from django.db import models


class Question(models.Model):
    """株式投資クイズの1問。questions.json の1要素をDBに移したもの。"""

    CATEGORY_CHOICES = [
        ("財務諸表分析", "財務諸表分析"),
        ("ファンダメンタルズ", "ファンダメンタルズ"),
        ("チャート分析", "チャート分析"),
    ]
    DIFFICULTY_CHOICES = [
        ("初級", "初級"),
        ("中級", "中級"),
        ("上級", "上級"),
    ]

    # questions.json の "id" をそのまま主キーに使う（移行の互換性のため）
    id = models.IntegerField(primary_key=True, verbose_name="問題ID")
    category = models.CharField("カテゴリ", max_length=50, choices=CATEGORY_CHOICES)
    difficulty = models.CharField("難易度", max_length=10, choices=DIFFICULTY_CHOICES)
    question = models.TextField("問題文")

    # 選択肢の配列は JSONField（SQLiteのJSON1で動作）
    options = models.JSONField("選択肢", default=list)
    answer = models.CharField("正解", max_length=255)
    hint = models.CharField("ヒント", max_length=255, blank=True, default="")
    explanation = models.TextField("解説", blank=True, default="")

    # 任意：チャート/財務データ問題への拡張用（無くてもよい）
    chart_data = models.JSONField("チャートデータ", null=True, blank=True)
    financial_data = models.JSONField("財務データ", null=True, blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "問題"
        verbose_name_plural = "問題"

    def __str__(self):
        return f"[{self.id}] {self.category}/{self.difficulty} {self.question[:30]}"