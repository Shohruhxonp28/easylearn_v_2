from django.db import models
import json


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='📚')

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Question(models.Model):
    SINGLE = 'single'
    MULTIPLE = 'multiple'
    TYPE_CHOICES = [(SINGLE, 'Single Choice'), (MULTIPLE, 'Multiple Choice')]

    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'
    DIFFICULTY_CHOICES = [(EASY, 'Easy'), (MEDIUM, 'Medium'), (HARD, 'Hard')]

    DRAFT = 'draft'
    PUBLISHED = 'published'
    STATUS_CHOICES = [(DRAFT, 'Draft'), (PUBLISHED, 'Published')]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='questions')
    title = models.CharField(max_length=300)
    body = models.TextField()
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=SINGLE)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default=MEDIUM)
    points = models.IntegerField(default=10)
    explanation = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title[:80]

    def get_options(self):
        return self.options.all()

    def get_correct_option_ids(self):
        return list(self.options.filter(is_correct=True).values_list('id', flat=True))


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.question.title[:40]} — {self.text[:40]}"
