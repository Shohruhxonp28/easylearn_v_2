from django.contrib import admin
from django.utils.html import format_html
from .models import Arena, ArenaParticipant, ArenaScore


class ArenaParticipantInline(admin.TabularInline):
    model = ArenaParticipant
    extra = 0
    readonly_fields = ('display_name', 'user', 'guest', 'joined_at')
    fields = ('display_name', 'user', 'joined_at', 'is_active')
    can_delete = False


@admin.register(Arena)
class ArenaAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status_badge', 'is_active', 'start_time', 'end_time', 'questions_per_match', 'bot_enabled', 'participant_count')
    list_filter = ('status', 'is_active', 'bot_enabled', 'difficulty')
    search_fields = ('title', 'description')
    list_per_page = 20
    inlines = [ArenaParticipantInline]
    actions = ['make_live', 'make_upcoming', 'make_finished', 'activate', 'deactivate']

    fieldsets = (
        ('🏟️ Arena', {
            'fields': ('title', 'description', 'category')
        }),
        ('⏰ Vaqt', {
            'fields': ('start_time', 'end_time', 'duration_minutes')
        }),
        ('⚙️ Sozlamalar', {
            'fields': ('questions_per_match', 'max_participants', 'difficulty', 'bot_enabled', 'is_active', 'status')
        }),
    )

    def status_badge(self, obj):
        colors = {
            'upcoming': ('#3498db', '⏳ Kutilmoqda'),
            'live':     ('#27ae60', '🟢 Jonli'),
            'finished': ('#95a5a6', '✅ Tugagan'),
        }
        color, label = colors.get(obj.status, ('#999', obj.status))
        return format_html('<span style="color:{};font-weight:bold">{}</span>', color, label)
    status_badge.short_description = 'Holati'

    @admin.action(description='🟢 Jonli (live) qilish')
    def make_live(self, request, queryset):
        queryset.update(status='live')

    @admin.action(description='⏳ Kutilmoqda qilish')
    def make_upcoming(self, request, queryset):
        queryset.update(status='upcoming')

    @admin.action(description='✅ Tugatish')
    def make_finished(self, request, queryset):
        queryset.update(status='finished')

    @admin.action(description='✔️ Faollashtirish')
    def activate(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='❌ O\'chirish (deactivate)')
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(ArenaParticipant)
class ArenaParticipantAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'arena', 'user', 'guest', 'joined_at', 'is_active')
    list_filter = ('arena', 'is_active')
    search_fields = ('display_name',)
    readonly_fields = ('joined_at',)


@admin.register(ArenaScore)
class ArenaScoreAdmin(admin.ModelAdmin):
    list_display = ('participant', 'arena', 'points', 'wins', 'losses', 'draws', 'total_matches')
    list_filter = ('arena',)
    ordering = ('-points',)
    readonly_fields = ('arena', 'participant', 'wins', 'losses', 'draws', 'points', 'total_matches')
