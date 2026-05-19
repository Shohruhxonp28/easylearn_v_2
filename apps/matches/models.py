from django.db import models
from django.utils import timezone
from apps.accounts.models import User, GuestParticipant
from apps.questions.models import Question, QuestionOption


class BotProfile(models.Model):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'
    LEVEL_CHOICES = [(EASY, 'Easy (50-60%)'), (MEDIUM, 'Medium (65-75%)'), (HARD, 'Hard (80-90%)')]

    name = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default=MEDIUM)
    avatar_initial = models.CharField(max_length=2, default='🤖')

    def get_correct_probability(self):
        import random
        if self.level == self.EASY:
            return random.uniform(0.50, 0.60)
        elif self.level == self.MEDIUM:
            return random.uniform(0.65, 0.75)
        else:
            return random.uniform(0.80, 0.90)

    def __str__(self):
        return f"{self.name} ({self.level})"


class Match(models.Model):
    DUEL = 'duel'
    ARENA = 'arena'
    TYPE_CHOICES = [(DUEL, 'Duel'), (ARENA, 'Arena')]

    WAITING = 'waiting'
    ACTIVE = 'active'
    FINISHED = 'finished'
    STATUS_CHOICES = [(WAITING, 'Waiting'), (ACTIVE, 'Active'), (FINISHED, 'Finished')]

    match_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=DUEL)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=WAITING)

    # Players
    player1 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='matches_as_p1')
    player2 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='matches_as_p2')
    guest_player = models.ForeignKey(GuestParticipant, on_delete=models.SET_NULL,
                                      null=True, blank=True)
    bot = models.ForeignKey(BotProfile, on_delete=models.SET_NULL, null=True, blank=True)

    # Arena link
    arena = models.ForeignKey('arenas.Arena', on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='matches')

    # Scores
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)

    # Progress
    current_question_index = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=5)

    # Result
    winner = models.CharField(max_length=20, blank=True)  # 'player1','player2','draw'

    # Category/difficulty
    category = models.ForeignKey('questions.Category', on_delete=models.SET_NULL,
                                  null=True, blank=True)
    difficulty = models.CharField(max_length=10, blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_player1_display(self):
        if self.player1:
            return self.player1.full_name or self.player1.username
        if self.guest_player:
            return self.guest_player.full_name
        return "Player 1"

    def get_player2_display(self):
        if self.player2:
            return self.player2.full_name or self.player2.username
        if self.bot:
            return f"🤖 {self.bot.name}"
        return "Player 2"

    def get_current_question(self):
        try:
            mq = self.match_questions.all()[self.current_question_index]
            return mq
        except IndexError:
            return None

    def is_player1(self, user):
        return self.player1 == user

    def is_player_in_match(self, user):
        return self.player1 == user or self.player2 == user

    def __str__(self):
        return f"Match #{self.id}: {self.get_player1_display()} vs {self.get_player2_display()}"


class MatchQuestion(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='match_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    # Bot answer cached here
    bot_answer_correct = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Match#{self.match_id} Q{self.order+1}: {self.question.title[:50]}"


class Submission(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='submissions')
    match_question = models.ForeignKey(MatchQuestion, on_delete=models.CASCADE,
                                        related_name='submissions')
    player = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    guest = models.ForeignKey(GuestParticipant, on_delete=models.SET_NULL, null=True, blank=True)
    is_bot = models.BooleanField(default=False)

    selected_options = models.ManyToManyField(QuestionOption, blank=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = []  # allow re-checking

    def __str__(self):
        who = self.player or self.guest or "Bot"
        return f"Submission by {who} on Match#{self.match_id}"
