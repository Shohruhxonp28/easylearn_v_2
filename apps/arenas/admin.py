from django.contrib import admin
from .models import Arena, ArenaParticipant, ArenaScore


@admin.register(Arena)
class ArenaAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'is_active', 'start_time', 'end_time', 'questions_per_match', 'bot_enabled', 'participant_count')
    list_filter = ('status', 'is_active', 'bot_enabled')
    search_fields = ('title',)
    


@admin.register(ArenaParticipant)
class ArenaParticipantAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'arena', 'user', 'guest', 'joined_at', 'is_active')
    list_filter = ('arena', 'is_active')
    search_fields = ('display_name',)


@admin.register(ArenaScore)
class ArenaScoreAdmin(admin.ModelAdmin):
    list_display = ('participant', 'arena', 'points', 'wins', 'losses', 'draws', 'total_matches')
    list_filter = ('arena',)
    ordering = ('-points',)
