from django.db import models
from django.conf import settings
from django.utils import timezone
from questions.models import Category


# ─── ARENA ────────────────────────────────────────────────────────────────────

class Arena(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('live', 'Live'),
        ('finished', 'Finished'),
    ]

    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    questions_per_match = models.IntegerField(default=5)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='upcoming')
    bot_enabled = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

    def get_status(self):
        """Dynamic status based on current time"""
        now = timezone.now()
        if now < self.start_time:
            return 'upcoming'
        elif now <= self.end_time:
            return 'live'
        return 'finished'

    def is_live(self):
        return self.get_status() == 'live'

    def is_upcoming(self):
        return self.get_status() == 'upcoming'


class ArenaRegistration(models.Model):
    arena = models.ForeignKey(Arena, on_delete=models.CASCADE, related_name='registrations')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('arena', 'student')

    def __str__(self):
        return f"{self.student.username} in {self.arena.title}"


class ArenaScore(models.Model):
    arena = models.ForeignKey(Arena, on_delete=models.CASCADE, related_name='scores')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    matches_played = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)

    class Meta:
        unique_together = ('arena', 'student')
        ordering = ['-points']

    def __str__(self):
        return f"{self.student.username}: {self.points} pts in {self.arena.title}"


# ─── TOURNAMENT ───────────────────────────────────────────────────────────────

class Tournament(models.Model):
    STATUS_CHOICES = [
        ('registration', 'Registration Open'),
        ('active', 'Active'),
        ('finished', 'Finished'),
    ]

    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    max_participants = models.IntegerField(choices=[(4,4),(8,8),(16,16)], default=8)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='registration')
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

    def participant_count(self):
        return self.participants.filter(is_active=True).count()

    def is_full(self):
        return self.participant_count() >= self.max_participants


class TournamentParticipant(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='participants')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_eliminated = models.BooleanField(default=False)
    seed = models.IntegerField(default=0)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tournament', 'student')

    def __str__(self):
        return f"{self.student.username} in {self.tournament.title}"


class TournamentRound(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='rounds')
    round_number = models.IntegerField()
    is_complete = models.BooleanField(default=False)

    class Meta:
        ordering = ['round_number']

    def __str__(self):
        return f"{self.tournament.title} - Round {self.round_number}"


class TournamentMatch(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('finished', 'Finished'),
        ('bye', 'BYE'),
    ]

    round = models.ForeignKey(TournamentRound, on_delete=models.CASCADE, related_name='matches')
    match = models.OneToOneField(
        'matches.Match', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tournament_match'
    )
    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='tournament_matches_p1'
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tournament_matches_p2'
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tournament_wins'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    bracket_position = models.IntegerField(default=0)

    class Meta:
        ordering = ['bracket_position']

    def __str__(self):
        p2 = self.player2.username if self.player2 else 'BYE'
        return f"Round {self.round.round_number}: {self.player1} vs {p2}"
