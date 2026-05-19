from django.db import models
from django.conf import settings
from questions.models import Question, Category


class BotProfile(models.Model):
    LEVEL_CHOICES = [
        ('easy', 'Easy (50% correct)'),
        ('medium', 'Medium (70% correct)'),
        ('hard', 'Hard (85% correct)'),
    ]
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='medium')
    avatar = models.CharField(max_length=100, default='🤖')

    def __str__(self):
        return f"{self.name} ({self.level})"

    def get_accuracy(self):
        if self.level == 'easy':
            return 0.5
        elif self.level == 'medium':
            return 0.7
        return 0.85


class DuelQueue(models.Model):
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='duel_queue'
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    difficulty = models.CharField(max_length=10, choices=[
        ('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')
    ])
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} waiting ({self.category.name}, {self.difficulty})"


class Match(models.Model):
    MATCH_TYPE_CHOICES = [
        ('duel', 'Duel'),
        ('arena', 'Arena'),
        ('tournament', 'Tournament'),
    ]
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('active', 'Active'),
        ('finished', 'Finished'),
    ]

    match_type = models.CharField(max_length=20, choices=MATCH_TYPE_CHOICES, default='duel')
    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='matches_as_p1'
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matches_as_p2'
    )
    bot = models.ForeignKey(BotProfile, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    difficulty = models.CharField(max_length=10, default='medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_matches'
    )
    is_draw = models.BooleanField(default=False)
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    player1_current_index = models.IntegerField(default=0)
    player2_current_index = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        p2 = self.player2.username if self.player2 else (self.bot.name if self.bot else '?')
        return f"{self.player1} vs {p2} ({self.match_type})"

    def get_opponent(self, player):
        """Return opponent for a given player"""
        if self.player1 == player:
            return self.player2 or self.bot
        return self.player1

    def get_opponent_name(self, player):
        if self.player1 == player:
            if self.player2:
                return self.player2.username
            if self.bot:
                return f"🤖 {self.bot.name}"
        else:
            return self.player1.username if self.player1 else '?'
        return '?'

    def player1_finished(self):
        return self.player1_current_index >= self.questions.count()

    def player2_finished(self):
        return self.player2_current_index >= self.questions.count()

    def both_finished(self):
        return self.player1_finished() and self.player2_finished()

    def get_current_question_for(self, player):
        """Return current MatchQuestion for a player, or None if done"""
        is_p1 = self.player1 == player
        idx = self.player1_current_index if is_p1 else self.player2_current_index
        try:
            return self.questions.order_by('order')[idx]
        except IndexError:
            return None

    def get_answered_count_for(self, player):
        is_p1 = self.player1 == player
        return self.player1_current_index if is_p1 else self.player2_current_index

    def total_questions(self):
        return self.questions.count()


class MatchQuestion(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    player1_answer = models.CharField(max_length=1, blank=True)
    player2_answer = models.CharField(max_length=1, blank=True)
    player1_answered = models.BooleanField(default=False)
    player2_answered = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def is_player1_correct(self):
        return self.player1_answer == self.question.correct_answer

    def is_player2_correct(self):
        return self.player2_answer == self.question.correct_answer
