from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, GuestParticipant


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'full_name', 'rating', 'wins', 'losses', 'draws', 'is_staff')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'full_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('full_name', 'rating', 'wins', 'losses', 'draws')}),
    )


@admin.register(GuestParticipant)
class GuestParticipantAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'session_key', 'created_at')
    search_fields = ('full_name',)
