from django.contrib import admin
from .models import DuelQueue


@admin.register(DuelQueue)
class DuelQueueAdmin(admin.ModelAdmin):
    list_display = ('player', 'category', 'difficulty', 'joined_at')
