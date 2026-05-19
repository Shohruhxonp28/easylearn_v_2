from django.contrib import admin
from .models import Category, Question, QuestionOption


class OptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    fields = ('text', 'is_correct', 'order')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'description')
    search_fields = ('name',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'question_type', 'difficulty', 'points', 'status')
    list_filter = ('category', 'question_type', 'difficulty', 'status')
    search_fields = ('title', 'body')
    inlines = [OptionInline]
    list_editable = ('status',)
    fieldsets = (
        ('Question', {'fields': ('category', 'title', 'body', 'question_type')}),
        ('Settings', {'fields': ('difficulty', 'points', 'status')}),
        ('Explanation', {'fields': ('explanation',)}),
    )
