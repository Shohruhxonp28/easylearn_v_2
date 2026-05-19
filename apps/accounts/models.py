from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    full_name = models.CharField(max_length=200, blank=True)
    rating = models.IntegerField(default=1000)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    avatar_initial = models.CharField(max_length=2, blank=True)

    def save(self, *args, **kwargs):
        if self.full_name:
            parts = self.full_name.strip().split()
            self.avatar_initial = ''.join(p[0].upper() for p in parts[:2])
        elif self.username:
            self.avatar_initial = self.username[:2].upper()
        super().save(*args, **kwargs)

    def total_matches(self):
        return self.wins + self.losses + self.draws

    def win_rate(self):
        total = self.total_matches()
        return round(self.wins / total * 100) if total > 0 else 0

    def update_rating(self, result):
        if result == 'win':
            self.rating += 10
            self.wins += 1
        elif result == 'loss':
            self.rating = max(0, self.rating - 5)
            self.losses += 1
        elif result == 'draw':
            self.rating += 2
            self.draws += 1
        self.save()

    def __str__(self):
        return self.full_name or self.username


class GuestParticipant(models.Model):
    full_name = models.CharField(max_length=200)
    session_key = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Guest: {self.full_name}"
