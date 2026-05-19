from django.contrib import admin
from django.utils import timezone
from .models import (
    Arena, ArenaRegistration, ArenaScore,
    Tournament, TournamentParticipant, TournamentRound, TournamentMatch
)
from .services import start_tournament


@admin.register(Arena)
class ArenaAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'start_time', 'end_time', 'status', 'bot_enabled')
    list_filter = ('status', 'category')
    search_fields = ('title',)


@admin.register(ArenaRegistration)
class ArenaRegistrationAdmin(admin.ModelAdmin):
    list_display = ('arena', 'student', 'registered_at')
    list_filter = ('arena',)


@admin.register(ArenaScore)
class ArenaScoreAdmin(admin.ModelAdmin):
    list_display = ('arena', 'student', 'points', 'wins', 'losses', 'draws', 'matches_played')
    list_filter = ('arena',)
    ordering = ('-points',)


class TournamentParticipantInline(admin.TabularInline):
    model = TournamentParticipant
    extra = 0
    readonly_fields = ('registered_at',)


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'start_time', 'max_participants', 'status', 'participant_count')
    list_filter = ('status', 'category')
    search_fields = ('title',)
    inlines = [TournamentParticipantInline]
    actions = ['action_start_tournament']

    def participant_count(self, obj):
        return obj.participant_count()

    def action_start_tournament(self, request, queryset):
        for tournament in queryset:
            success, msg = start_tournament(tournament)
            if success:
                self.message_user(request, f'{tournament.title}: {msg}')
            else:
                self.message_user(request, f'{tournament.title}: {msg}', level='error')
    action_start_tournament.short_description = 'Start selected tournaments'


@admin.register(TournamentParticipant)
class TournamentParticipantAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'student', 'is_active', 'is_eliminated', 'registered_at')
    list_filter = ('tournament', 'is_eliminated')


class TournamentMatchInline(admin.TabularInline):
    model = TournamentMatch
    extra = 0
    readonly_fields = ('player1', 'player2', 'winner', 'status', 'match')


@admin.register(TournamentRound)
class TournamentRoundAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'round_number', 'is_complete')
    inlines = [TournamentMatchInline]


@admin.register(TournamentMatch)
class TournamentMatchAdmin(admin.ModelAdmin):
    list_display = ('round', 'player1', 'player2', 'winner', 'status', 'bracket_position')
    list_filter = ('status', 'round__tournament')
