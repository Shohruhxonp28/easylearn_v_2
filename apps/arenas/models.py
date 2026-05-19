from django.db import models
from django.utils import timezone
from apps.accounts.models import User, GuestParticipant
from apps.questions.models import Category


class Arena(models.Model):
    UPCOMING = 'upcoming'
    LIVE = 'live'
    FINISHED = 'finished'
    STATUS_CHOICES = [(UPCOMING, 'Upcoming'), (LIVE, 'Live'), (FINISHED, 'Finished')]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    questions_per_match = models.IntegerField(default=5)
    max_participants = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    bot_enabled = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=UPCOMING)
    difficulty = models.CharField(max_length=10, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)

    def update_status(self):
        now = timezone.now()
        if now < self.start_time:
            self.status = self.UPCOMING
        elif self.start_time <= now <= self.end_time:
            self.status = self.LIVE
        else:
            self.status = self.FINISHED
        self.save(update_fields=['status'])

    def is_live(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    def time_remaining_seconds(self):
        now = timezone.now()
        if now < self.end_time:
            return int((self.end_time - now).total_seconds())
        return 0

    def participant_count(self):
        return self.participants.count()

    def __str__(self):
        return self.title


class ArenaParticipant(models.Model):
    arena = models.ForeignKey(Arena, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    guest = models.ForeignKey(GuestParticipant, on_delete=models.SET_NULL, null=True, blank=True)
    display_name = models.CharField(max_length=200)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # currently in arena window
    current_match = models.ForeignKey('matches.Match', on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='+')

    class Meta:
        unique_together = [['arena', 'user'], ['arena', 'guest']]

    def __str__(self):
        return f"{self.display_name} in {self.arena.title}"


class ArenaScore(models.Model):
    arena = models.ForeignKey(Arena, on_delete=models.CASCADE, related_name='scores')
    participant = models.ForeignKey(ArenaParticipant, on_delete=models.CASCADE,
                                    related_name='score')
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    total_matches = models.IntegerField(default=0)

    class Meta:
        unique_together = [['arena', 'participant']]
        ordering = ['-points', '-wins']

    def update_result(self, result):
        if result == 'win':
            self.wins += 1
            self.points += 2
        elif result == 'loss':
            self.losses += 1
        elif result == 'draw':
            self.draws += 1
            self.points += 1
        self.total_matches += 1
        self.save()

    def __str__(self):
        return f"{self.participant.display_name}: {self.points}pts in {self.arena.title}"
