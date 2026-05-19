from django.contrib import admin
from .models import Match, MatchQuestion, BotProfile, DuelQueue


class MatchQuestionInline(admin.TabularInline):
    model = MatchQuestion
    extra = 0
    readonly_fields = ('question', 'player1_answer', 'player2_answer', 'player1_answered', 'player2_answered')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'match_type', 'player1', 'player2', 'bot', 'status', 'winner', 'player1_score', 'player2_score', 'started_at')
    list_filter = ('match_type', 'status', 'difficulty')
    search_fields = ('player1__username', 'player2__username')
    inlines = [MatchQuestionInline]
    readonly_fields = ('started_at', 'ended_at')


@admin.register(BotProfile)
class BotProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'avatar')


@admin.register(DuelQueue)
class DuelQueueAdmin(admin.ModelAdmin):
    list_display = ('student', 'category', 'difficulty', 'joined_at')
