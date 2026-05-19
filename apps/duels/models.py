from django.db import models
from apps.accounts.models import User
from apps.questions.models import Category


class DuelQueue(models.Model):
    player = models.OneToOneField(User, on_delete=models.CASCADE, related_name='duel_queue')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    difficulty = models.CharField(max_length=10, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player} waiting ({self.category})"
