from django.contrib.auth.models import AbstractUser
from django.db import models


class Student(AbstractUser):
    full_name = models.CharField(max_length=200, blank=True)
    school = models.CharField(max_length=200, blank=True)
    group = models.CharField(max_length=100, blank=True)
    rating = models.IntegerField(default=1000)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)

    def __str__(self):
        return self.username

    def update_result(self, result):
        """result: 'win', 'loss', 'draw'"""
        if result == 'win':
            self.wins += 1
            self.rating += 10
        elif result == 'loss':
            self.losses += 1
            self.rating = max(0, self.rating - 5)
        elif result == 'draw':
            self.draws += 1
            self.rating += 2
        self.save()

    @property
    def total_matches(self):
        return self.wins + self.losses + self.draws

    @property
    def rank_info(self):
        r = self.rating
        if r < 1200:
            return {"code": "NF", "name": "Neofit", "color": "#475569", "bg": "#F1F5F9"}
        elif r < 1400:
            return {"code": "RT", "name": "Ritor", "color": "#047857", "bg": "#D1FAE5"}
        elif r < 1600:
            return {"code": "MG", "name": "Magistr", "color": "#6D28D9", "bg": "#F3E8FF"}
        elif r < 1800:
            return {"code": "L2", "name": "Legat", "color": "#1D4ED8", "bg": "#DBEAFE"}
        elif r < 2000:
            return {"code": "L1", "name": "Liktor", "color": "#1E3A8A", "bg": "#BFDBFE"}
        else:
            return {"code": "GM", "name": "Pretor", "color": "#B91C1C", "bg": "#FEE2E2"}
