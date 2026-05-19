from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.matches.models import Match, MatchQuestion, Submission
from apps.matches.services import submit_answer, finish_match
from apps.accounts.models import GuestParticipant


def _get_guest(request, match):
    """Return GuestParticipant if relevant to this match."""
    guest_id = request.session.get('guest_id')
    if guest_id and match.guest_player_id:
        return GuestParticipant.objects.filter(id=guest_id).first()
    return None


def match_play(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    if match.status == 'finished':
        return redirect('match_result', match_id=match_id)

    if match.status == 'waiting':
        return render(request, 'matches/waiting.html', {'match': match})

    player = request.user if request.user.is_authenticated else None
    guest = _get_guest(request, match)

    mq = match.get_current_question()
    if mq is None:
        finish_match(match)
        return redirect('match_result', match_id=match_id)

    # Check already submitted
    already_submitted = False
    if player:
        already_submitted = Submission.objects.filter(
            match=match, match_question=mq, player=player
        ).exists()
    elif guest:
        already_submitted = Submission.objects.filter(
            match=match, match_question=mq, guest=guest
        ).exists()

    if already_submitted:
        # Move forward if already answered (e.g., page refresh)
        return redirect('match_result' if match.status == 'finished' else 'match_play',
                        match_id=match_id)

    all_questions = list(match.match_questions.all())
    options = mq.question.get_options()

    return render(request, 'matches/play.html', {
        'match': match,
        'match_question': mq,
        'question': mq.question,
        'options': options,
        'all_questions': all_questions,
        'q_num': match.current_question_index + 1,
        'total': match.total_questions,
        'player': player,
        'guest': guest,
    })


@require_POST
def submit_answer_view(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    if match.status == 'finished':
        return JsonResponse({'done': True, 'redirect': f'/matches/{match_id}/result/'})

    mq = match.get_current_question()
    if mq is None:
        finish_match(match)
        return JsonResponse({'done': True, 'redirect': f'/matches/{match_id}/result/'})

    player = request.user if request.user.is_authenticated else None
    guest = _get_guest(request, match)

    # Prevent double submission
    if player and Submission.objects.filter(match=match, match_question=mq, player=player).exists():
        return JsonResponse({'error': 'Already submitted'}, status=400)
    if guest and Submission.objects.filter(match=match, match_question=mq, guest=guest).exists():
        return JsonResponse({'error': 'Already submitted'}, status=400)

    selected_ids = request.POST.getlist('options')
    result = submit_answer(match, mq, player=player, guest=guest, selected_option_ids=selected_ids)

    if result['done']:
        return JsonResponse({
            'done': True,
            'redirect': f'/matches/{match_id}/result/',
            'is_correct': result['is_correct'],
            'points': result['points'],
            'correct_ids': result['correct_ids'],
            'explanation': result['explanation'],
        })

    return JsonResponse({
        'done': False,
        'is_correct': result['is_correct'],
        'points': result['points'],
        'correct_ids': result['correct_ids'],
        'explanation': result['explanation'],
        'next_url': f'/matches/{match_id}/play/',
    })


def match_result(request, match_id):
    match = get_object_or_404(Match, id=match_id, status='finished')
    player = request.user if request.user.is_authenticated else None
    guest = _get_guest(request, match)

    q_results = []
    for mq in match.match_questions.select_related('question').prefetch_related(
            'question__options', 'submissions__selected_options'):
        sub = None
        if player:
            sub = mq.submissions.filter(player=player).first()
        elif guest:
            sub = mq.submissions.filter(guest=guest).first()
        q_results.append({
            'question': mq.question,
            'submission': sub,
            'correct_option_ids': mq.question.get_correct_option_ids(),
            'options': list(mq.question.options.all()),
        })

    return render(request, 'matches/result.html', {
        'match': match,
        'q_results': q_results,
        'player': player,
        'guest': guest,
    })
