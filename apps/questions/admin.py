from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Question, QuestionOption


class OptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    min_num = 2
    max_num = 6
    fields = ('text', 'is_correct', 'order')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'description', 'question_count')
    search_fields = ('name',)

    def question_count(self, obj):
        count = obj.questions.count()
        return format_html('<b>{}</b> ta savol', count)
    question_count.short_description = 'Savollar'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'question_type', 'difficulty_badge', 'points', 'option_count', 'status')
    list_filter = ('category', 'difficulty', 'status', 'question_type')
    search_fields = ('title', 'body')
    inlines = [OptionInline]
    list_editable = ('status',)
    list_per_page = 25
    actions = ['make_published', 'make_draft']

    fieldsets = (
        ('📝 Savol', {'fields': ('category', 'title', 'body', 'question_type')}),
        ('⚙️ Sozlamalar', {'fields': ('difficulty', 'points', 'status')}),
        ('💡 Tushuntirish', {'fields': ('explanation',), 'classes': ('collapse',)}),
    )

    def difficulty_badge(self, obj):
        colors = {'easy': '#27ae60', 'medium': '#f39c12', 'hard': '#e74c3c'}
        labels = {'easy': '🟢 Oson', 'medium': '🟡 O\'rta', 'hard': '🔴 Qiyin'}
        color = colors.get(obj.difficulty, '#999')
        label = labels.get(obj.difficulty, obj.difficulty)
        return format_html('<span style="color:{};font-weight:bold">{}</span>', color, label)
    difficulty_badge.short_description = 'Darajasi'

    def option_count(self, obj):
        total = obj.options.count()
        correct = obj.options.filter(is_correct=True).count()
        color = '#27ae60' if correct >= 1 else '#e74c3c'
        return format_html('<span style="color:{}">{} / {} ✓</span>', color, correct, total)
    option_count.short_description = 'To\'g\'ri/Jami'

    @admin.action(description='✅ Tanlangan savollarni nashr qilish')
    def make_published(self, request, queryset):
        queryset.update(status='published')

    @admin.action(description='📝 Tanlangan savollarni qoralamaga o\'tkazish')
    def make_draft(self, request, queryset):
        queryset.update(status='draft')
