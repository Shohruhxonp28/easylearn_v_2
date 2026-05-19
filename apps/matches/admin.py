from django.contrib import admin
from .models import Match, MatchQuestion, Submission, BotProfile


@admin.register(BotProfile)
class BotProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'avatar_initial')


class MatchQuestionInline(admin.TabularInline):
    model = MatchQuestion
    extra = 0
    readonly_fields = ('question', 'order', 'bot_answer_correct')


class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0
    readonly_fields = ('player', 'guest', 'is_bot', 'is_correct', 'points_earned')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'match_type', 'status', 'player1', 'player2', 'bot',
                    'player1_score', 'player2_score', 'winner', 'created_at')
    list_filter = ('match_type', 'status', 'winner')
    search_fields = ('player1__username', 'player2__username')
    inlines = [MatchQuestionInline, SubmissionInline]
    readonly_fields = ('created_at', 'started_at', 'ended_at')


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'match', 'player', 'guest', 'is_correct', 'points_earned')
    list_filter = ('is_correct',)
