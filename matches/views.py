from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from questions.models import Category
from .models import Match, MatchQuestion, DuelQueue
from .services import find_or_create_duel, submit_answer_and_advance, maybe_finalize, finalize_match


@login_required
def duel_lobby(request):
    categories = Category.objects.all()
    student = request.user
    active_match = Match.objects.filter(
        Q(player1=student) | Q(player2=student), status='active', match_type='duel'
    ).first()
    in_queue = DuelQueue.objects.filter(student=student).first()

    # Recent battles
    recent = Match.objects.filter(
        Q(player1=student) | Q(player2=student), status='finished'
    ).order_by('-ended_at')[:5]

    # Waiting room — others in queue (not current user)
    waiting_room = DuelQueue.objects.exclude(student=student).select_related('student', 'category').order_by('joined_at')[:10]

    return render(request, 'matches/duel_lobby.html', {
        'categories': categories,
        'active_match': active_match,
        'in_queue': in_queue,
        'recent': recent,
        'waiting_room': waiting_room,
    })


@login_required
def start_duel(request):
    if request.method != 'POST':
        return redirect('duel_lobby')
    student = request.user
    category_id = request.POST.get('category')
    difficulty = request.POST.get('difficulty', 'medium')
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        messages.error(request, 'Invalid category.')
        return redirect('duel_lobby')

    match, status = find_or_create_duel(student, category, difficulty)

    if status == 'already_in_match':
        messages.warning(request, 'You already have an active match!')
        active = Match.objects.filter(Q(player1=student) | Q(player2=student), status='active').first()
        if active:
            return redirect('match_play', match_id=active.id)
        return redirect('duel_lobby')
    if status == 'already_in_queue':
        messages.info(request, 'You are already in the queue.')
        return redirect('duel_lobby')
    if match is None:
        messages.error(request, 'No questions found for this category/difficulty. Ask admin to add questions.')
        return redirect('duel_lobby')

    return redirect('match_play', match_id=match.id)


@login_required
def match_play(request, match_id):
    """One-by-one question flow"""
    student = request.user
    match = get_object_or_404(Match, id=match_id)

    if match.player1 != student and match.player2 != student:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if match.status == 'finished':
        return redirect('match_result', match_id=match.id)

    is_p1 = match.player1 == student
    current_idx = match.player1_current_index if is_p1 else match.player2_current_index
    total = match.total_questions()

    # Check if player is done
    if current_idx >= total:
        # Player finished — wait for opponent or finalize
        if maybe_finalize(match):
            match.refresh_from_db()
            return redirect('match_result', match_id=match.id)
        # Still waiting for opponent in pvp
        return render(request, 'matches/match_waiting.html', {
            'match': match,
            'opponent_name': match.get_opponent_name(student),
            'total': total,
        })

    # Get current question
    qs_list = list(match.questions.order_by('order'))
    current_mq = qs_list[current_idx]

    if request.method == 'POST':
        answer = request.POST.get('answer', '').strip().upper()
        if answer not in ['A', 'B', 'C', 'D']:
            messages.error(request, 'Please select an answer.')
            return redirect('match_play', match_id=match_id)

        success, player_done, msg = submit_answer_and_advance(match, student, current_idx, answer)
        if not success:
            messages.error(request, msg)
            return redirect('match_play', match_id=match_id)

        if player_done:
            if maybe_finalize(match):
                return redirect('match_result', match_id=match.id)
            # PvP — waiting for opponent
            return render(request, 'matches/match_waiting.html', {
                'match': match,
                'opponent_name': match.get_opponent_name(student),
                'total': total,
            })

        return redirect('match_play', match_id=match_id)

    # Build answered list for sidebar progress (both players)
    answered = []
    for i, mq in enumerate(qs_list):
        answered.append({
            'n': i + 1,
            'p1_answered': mq.player1_answered,
            'p1_correct': mq.is_player1_correct() if mq.player1_answered else False,
            'p2_answered': mq.player2_answered,
            'p2_correct': mq.is_player2_correct() if mq.player2_answered else False,
            'is_current_p1': i == match.player1_current_index,
            'is_current_p2': i == match.player2_current_index,
            'is_current_user': i == current_idx,
        })

    # Running score
    p1_score = sum(mq.question.points for mq in qs_list[:current_idx] if is_p1 and mq.is_player1_correct()
                   or not is_p1 and False)
    my_score = 0
    for i, mq in enumerate(qs_list):
        if i >= current_idx:
            break
        if is_p1 and mq.is_player1_correct():
            my_score += mq.question.points
        elif not is_p1 and mq.is_player2_correct():
            my_score += mq.question.points

    diff_colors = {'easy': 'success', 'medium': 'warning', 'hard': 'danger'}

    return render(request, 'matches/match_play.html', {
        'match': match,
        'current_mq': current_mq,
        'question': current_mq.question,
        'options': current_mq.question.get_options(),
        'current_idx': current_idx,
        'total': total,
        'answered': answered,
        'my_score': my_score,
        'opponent_name': match.get_opponent_name(student),
        'is_p1': is_p1,
        'diff_color': diff_colors.get(match.difficulty, 'secondary'),
    })


@login_required
def match_result(request, match_id):
    student = request.user
    match = get_object_or_404(Match, id=match_id)

    if match.player1 != student and match.player2 != student:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if match.status != 'finished':
        finalize_match(match)
        match.refresh_from_db()

    is_p1 = match.player1 == student
    my_score = match.player1_score if is_p1 else match.player2_score
    opp_score = match.player2_score if is_p1 else match.player1_score
    opponent_name = match.get_opponent_name(student)

    if match.is_draw:
        result = 'draw'
        rating_change = '+2'
    elif match.winner == student:
        result = 'win'
        rating_change = '+10'
    else:
        result = 'loss'
        rating_change = '-5'

    review = []
    for mq in match.questions.order_by('order'):
        my_ans = mq.player1_answer if is_p1 else mq.player2_answer
        opp_ans = mq.player2_answer if is_p1 else mq.player1_answer
        correct = my_ans == mq.question.correct_answer
        review.append({
            'question': mq.question,
            'options': mq.question.get_options(),
            'my_answer': my_ans,
            'opp_answer': opp_ans,
            'correct_answer': mq.question.correct_answer,
            'is_correct': correct,
        })

    return render(request, 'matches/match_result.html', {
        'match': match,
        'my_score': my_score,
        'opp_score': opp_score,
        'opponent_name': opponent_name,
        'result': result,
        'rating_change': rating_change,
        'review': review,
        'student': student,
    })


@login_required
def leave_queue(request):
    DuelQueue.objects.filter(student=request.user).delete()
    messages.info(request, 'Left the queue.')
    return redirect('duel_lobby')
