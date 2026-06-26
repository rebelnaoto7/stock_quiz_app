from django.contrib import admin

from .models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "difficulty", "question", "answer")
    list_filter = ("category", "difficulty")
    search_fields = ("question", "answer", "explanation")
    ordering = ("id",)