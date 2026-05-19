import random
from django.utils import timezone
from apps.questions.models import Question, QuestionOption
from apps.matches.models import Match, MatchQuestion, Submission, BotProfile


def get_questions_for_match(category=None, difficulty=None, count=5):
    qs = Question.objects.filter(status='published')
    if category:
        qs = qs.filter(category=category)
    if difficulty and difficulty in ('easy', 'medium', 'hard'):
        qs = qs.filter(difficulty=difficulty)
    questions = list(qs.prefetch_related('options'))
    if len(questions) < count:
        count = len(questions)
    if count == 0:
        return []
    return random.sample(questions, count)


def create_match_questions(match, questions):
    mqs = []
    for i, q in enumerate(questions):
        bot_correct = None
        if match.bot:
            prob = match.bot.get_correct_probability()
            bot_correct = random.random() < prob
        mqs.append(MatchQuestion(
            match=match,
            question=q,
            order=i,
            bot_answer_correct=bot_correct,
        ))
    MatchQuestion.objects.bulk_create(mqs)


def submit_answer(match, match_question, player=None, guest=None, selected_option_ids=None):
    """Process player answer. Returns result dict."""
    if selected_option_ids is None:
        selected_option_ids = []

    question = match_question.question
    correct_ids = set(question.get_correct_option_ids())
    selected_ids = set(int(i) for i in selected_option_ids if str(i).isdigit())

    is_correct = (correct_ids == selected_ids) and bool(selected_ids)
    points = question.points if is_correct else 0

    sub = Submission.objects.create(
        match=match,
        match_question=match_question,
        player=player,
        guest=guest,
        is_correct=is_correct,
        points_earned=points,
    )
    if selected_option_ids:
        opts = QuestionOption.objects.filter(id__in=selected_ids)
        sub.selected_options.set(opts)

    # Determine if this is player1
    is_p1 = False
    if player and match.player1 == player:
        is_p1 = True
    elif guest and match.guest_player == guest:
        is_p1 = True  # guest is always player1 in arena

    if is_p1:
        match.player1_score += points
    else:
        match.player2_score += points

    match.current_question_index += 1
    all_done = match.current_question_index >= match.total_questions

    if all_done:
        finish_match(match)
    else:
        match.save(update_fields=['player1_score', 'player2_score', 'current_question_index'])

    return {
        'is_correct': is_correct,
        'points': points,
        'correct_ids': list(correct_ids),
        'done': all_done,
        'explanation': question.explanation,
    }


def finish_match(match):
    match.status = Match.FINISHED
    match.ended_at = timezone.now()

    p1 = match.player1_score
    p2 = match.player2_score

    if p1 > p2:
        match.winner = 'player1'
    elif p2 > p1:
        match.winner = 'player2'
    else:
        match.winner = 'draw'

    match.save(update_fields=[
        'status', 'ended_at', 'winner',
        'player1_score', 'player2_score', 'current_question_index'
    ])

    # Update registered user ratings (only for registered vs registered or vs bot)
    _update_user_ratings(match)

    # Update arena scores if arena match
    if match.arena_id:
        _update_arena_scores(match)

    return match


def _update_user_ratings(match):
    """Update rating for registered users after match."""
    if match.player1 and match.bot:
        # vs bot
        if match.winner == 'player1':
            match.player1.update_rating('win')
        elif match.winner == 'player2':
            match.player1.update_rating('loss')
        else:
            match.player1.update_rating('draw')

    elif match.player1 and match.player2:
        # pvp
        if match.winner == 'player1':
            match.player1.update_rating('win')
            match.player2.update_rating('loss')
        elif match.winner == 'player2':
            match.player1.update_rating('loss')
            match.player2.update_rating('win')
        else:
            match.player1.update_rating('draw')
            match.player2.update_rating('draw')


def _update_arena_scores(match):
    from apps.arenas.models import ArenaParticipant, ArenaScore
    arena = match.arena

    # Find participant 1
    p1_participant = None
    if match.player1:
        p1_participant = ArenaParticipant.objects.filter(arena=arena, user=match.player1).first()
    elif match.guest_player:
        p1_participant = ArenaParticipant.objects.filter(arena=arena, guest=match.guest_player).first()

    if not p1_participant:
        return

    p1_score, _ = ArenaScore.objects.get_or_create(arena=arena, participant=p1_participant)

    result_for_p1 = match.winner  # 'player1', 'player2', or 'draw'
    if result_for_p1 == 'player1':
        p1_score.update_result('win')
    elif result_for_p1 == 'player2':
        p1_score.update_result('loss')
    else:
        p1_score.update_result('draw')

    # Clear current match so player can start new battle
    p1_participant.current_match = None
    p1_participant.save(update_fields=['current_match'])
