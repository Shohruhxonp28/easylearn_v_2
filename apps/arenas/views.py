from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from apps.arenas.models import Arena, ArenaParticipant, ArenaScore
from apps.arenas.services import join_arena, start_arena_battle
from apps.accounts.models import GuestParticipant
from apps.matches.models import Match


def arena_list(request):
    arenas = Arena.objects.filter(is_active=True).order_by('-start_time')
    for a in arenas:
        a.update_status()
    return render(request, 'arenas/list.html', {'arenas': arenas})


def arena_detail(request, arena_id):
    arena = get_object_or_404(Arena, id=arena_id, is_active=True)
    arena.update_status()
    scores = ArenaScore.objects.filter(arena=arena).select_related(
        'participant'
    ).order_by('-points', '-wins')[:20]
    return render(request, 'arenas/detail.html', {
        'arena': arena,
        'scores': scores,
    })


def arena_join(request, arena_id):
    arena = get_object_or_404(Arena, id=arena_id, is_active=True)
    arena.update_status()

    if arena.status != 'live':
        messages.error(request, 'Arena is not live yet.')
        return redirect('arena_detail', arena_id=arena_id)

    if request.user.is_authenticated:
        participant = join_arena(arena, user=request.user,
                                  display_name=request.user.full_name or request.user.username)
        request.session[f'arena_{arena_id}_participant'] = participant.id
        return redirect('arena_live', arena_id=arena_id)

    # Guest flow
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        if not full_name:
            messages.error(request, 'Please enter your name.')
            return redirect('arena_join', arena_id=arena_id)

        guest = GuestParticipant.objects.create(
            full_name=full_name,
            session_key=request.session.session_key or '',
        )
        participant = join_arena(arena, guest=guest, display_name=full_name)
        request.session[f'arena_{arena_id}_participant'] = participant.id
        request.session[f'arena_{arena_id}_guest'] = guest.id
        return redirect('arena_live', arena_id=arena_id)

    return render(request, 'arenas/join.html', {'arena': arena})


def arena_live(request, arena_id):
    arena = get_object_or_404(Arena, id=arena_id)
    arena.update_status()

    participant_id = request.session.get(f'arena_{arena_id}_participant')
    if not participant_id:
        return redirect('arena_join', arena_id=arena_id)

    participant = get_object_or_404(ArenaParticipant, id=participant_id)
    my_score = ArenaScore.objects.filter(arena=arena, participant=participant).first()
    scores = ArenaScore.objects.filter(arena=arena).select_related(
        'participant'
    ).order_by('-points', '-wins')[:20]

    # Check if there's an active match
    active_match = None
    if participant.current_match and participant.current_match.status == 'active':
        active_match = participant.current_match

    return render(request, 'arenas/live.html', {
        'arena': arena,
        'participant': participant,
        'my_score': my_score,
        'scores': scores,
        'active_match': active_match,
        'time_remaining': arena.time_remaining_seconds(),
    })


def arena_start_battle(request, arena_id):
    if request.method != 'POST':
        return redirect('arena_live', arena_id=arena_id)

    arena = get_object_or_404(Arena, id=arena_id)
    arena.update_status()

    if not arena.is_live():
        messages.error(request, 'Arena has ended.')
        return redirect('arena_detail', arena_id=arena_id)

    participant_id = request.session.get(f'arena_{arena_id}_participant')
    if not participant_id:
        return redirect('arena_join', arena_id=arena_id)

    participant = get_object_or_404(ArenaParticipant, id=participant_id)

    match = start_arena_battle(arena, participant)
    if not match:
        messages.warning(request, 'No questions available. Ask admin to add questions.')
        return redirect('arena_live', arena_id=arena_id)

    return redirect('match_play', match_id=match.id)


def arena_leaderboard(request, arena_id):
    arena = get_object_or_404(Arena, id=arena_id)
    scores = ArenaScore.objects.filter(arena=arena).select_related(
        'participant'
    ).order_by('-points', '-wins', '-draws')
    return render(request, 'arenas/leaderboard.html', {
        'arena': arena,
        'scores': scores,
    })
