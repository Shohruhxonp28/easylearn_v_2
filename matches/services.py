import random
from django.utils import timezone
from django.db import transaction
from questions.models import Question
from .models import Match, MatchQuestion, BotProfile, DuelQueue


QUESTIONS_PER_DUEL = 5


def get_or_create_default_bot(level='medium'):
    bot, _ = BotProfile.objects.get_or_create(
        level=level,
        defaults={'name': f'{level.capitalize()} Bot', 'avatar': '🤖'}
    )
    return bot


def get_questions_for_match(category, difficulty, count=QUESTIONS_PER_DUEL):
    qs = Question.objects.filter(category=category, difficulty=difficulty, status='published')
    if qs.count() == 0:
        qs = Question.objects.filter(category=category, status='published')
    total = qs.count()
    if total == 0:
        return []
    count = min(count, total)
    return random.sample(list(qs), count)


@transaction.atomic
def find_or_create_duel(student, category, difficulty):
    from django.db.models import Q
    active = Match.objects.filter(Q(player1=student) | Q(player2=student), status='active').first()
    if active:
        return None, 'already_in_match'
    if DuelQueue.objects.filter(student=student).exists():
        return None, 'already_in_queue'
    waiting = DuelQueue.objects.filter(
        category=category, difficulty=difficulty
    ).exclude(student=student).select_for_update().first()
    if waiting:
        opponent = waiting.student
        waiting.delete()
        match = create_match(student, opponent, category, difficulty, 'duel')
        return match, 'match_found'
    else:
        bot = get_or_create_default_bot(difficulty)
        match = create_match(student, None, category, difficulty, 'duel', bot=bot)
        return match, 'bot_match'


@transaction.atomic
def create_match(player1, player2, category, difficulty, match_type, bot=None, count=QUESTIONS_PER_DUEL):
    questions = get_questions_for_match(category, difficulty, count)
    if not questions:
        return None
    match = Match.objects.create(
        match_type=match_type, player1=player1, player2=player2,
        bot=bot, category=category, difficulty=difficulty, status='active',
        player1_current_index=0, player2_current_index=0,
    )
    for i, q in enumerate(questions):
        MatchQuestion.objects.create(match=match, question=q, order=i)
    if bot:
        simulate_bot_answers(match, bot)
    return match


def simulate_bot_answers(match, bot):
    accuracy = bot.get_accuracy()
    for mq in match.questions.all():
        correct = mq.question.correct_answer
        options = ['A', 'B', 'C', 'D']
        answer = correct if random.random() < accuracy else random.choice([o for o in options if o != correct])
        mq.player2_answer = answer
        mq.player2_answered = True
        mq.save()
    total = match.questions.count()
    Match.objects.filter(pk=match.pk).update(player2_current_index=total)


@transaction.atomic
def submit_answer_and_advance(match, player, question_order, answer):
    """
    One-by-one flow: validate order, save answer, advance index.
    Returns (success, player_is_finished, message)
    """
    is_p1 = match.player1 == player
    current_idx = match.player1_current_index if is_p1 else match.player2_current_index

    if question_order != current_idx:
        return False, False, 'Wrong question order'

    qs_list = list(match.questions.order_by('order'))
    if current_idx >= len(qs_list):
        return False, True, 'No more questions'

    mq = qs_list[current_idx]

    if is_p1 and mq.player1_answered:
        return False, False, 'Already answered'
    if not is_p1 and mq.player2_answered:
        return False, False, 'Already answered'

    if is_p1:
        mq.player1_answer = answer
        mq.player1_answered = True
    else:
        mq.player2_answer = answer
        mq.player2_answered = True
    mq.save()

    new_idx = current_idx + 1
    if is_p1:
        match.player1_current_index = new_idx
    else:
        match.player2_current_index = new_idx
    match.save(update_fields=['player1_current_index', 'player2_current_index'])

    is_done = new_idx >= len(qs_list)
    return True, is_done, 'Answer saved'


def calculate_scores(match):
    p1, p2 = 0, 0
    for mq in match.questions.all():
        if mq.is_player1_correct():
            p1 += mq.question.points
        if mq.is_player2_correct():
            p2 += mq.question.points
    return p1, p2


@transaction.atomic
def finalize_match(match):
    if match.status == 'finished':
        return
    p1_score, p2_score = calculate_scores(match)
    match.player1_score = p1_score
    match.player2_score = p2_score
    match.status = 'finished'
    match.ended_at = timezone.now()
    player1 = match.player1
    if p1_score > p2_score:
        match.winner = player1
        match.is_draw = False
        if player1: player1.update_result('win')
        if match.player2: match.player2.update_result('loss')
    elif p2_score > p1_score:
        match.is_draw = False
        if match.player2:
            match.winner = match.player2
            match.player2.update_result('win')
        if player1: player1.update_result('loss')
    else:
        match.winner = None
        match.is_draw = True
        if player1: player1.update_result('draw')
        if match.player2: match.player2.update_result('draw')
    match.save()


def maybe_finalize(match):
    match.refresh_from_db()
    if match.bot and match.player1_finished():
        finalize_match(match)
        return True
    if not match.bot and match.player1_finished() and match.player2_finished():
        finalize_match(match)
        return True
    return False
