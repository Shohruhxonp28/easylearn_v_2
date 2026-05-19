from django.contrib import admin
from .models import Category, Question, QuestionOption


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    max_num = 4


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'points', 'correct_answer', 'status')
    list_filter = ('category', 'difficulty', 'status')
    search_fields = ('title', 'body')
    list_editable = ('status',)
    inlines = [QuestionOptionInline]
    fieldsets = (
        (None, {'fields': ('category', 'title', 'body', 'difficulty', 'points')}),
        ('Answer', {'fields': ('correct_answer', 'explanation')}),
        ('Publishing', {'fields': ('status',)}),
    )
