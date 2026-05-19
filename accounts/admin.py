from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Student


@admin.register(Student)
class StudentAdmin(UserAdmin):
    list_display = ('username', 'full_name', 'school', 'group', 'rating', 'wins', 'losses', 'draws')
    list_filter = ('school', 'is_staff', 'is_active')
    search_fields = ('username', 'full_name', 'school')
    fieldsets = UserAdmin.fieldsets + (
        ('Student Info', {'fields': ('full_name', 'school', 'group', 'rating', 'wins', 'losses', 'draws')}),
    )
