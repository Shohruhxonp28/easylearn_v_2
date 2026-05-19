from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from apps.arenas.models import Arena, ArenaParticipant, ArenaScore
from apps.arenas.services import join_arena, start_arena_battle
from apps.accounts.models import GuestParticipant
from apps.matches.models import Match
from apps.questions.models import Category


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Bu sahifaga kirish huquqingiz yo\'q.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@staff_required
def arena_create(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category') or None
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        duration_minutes = int(request.POST.get('duration_minutes', 60))
        questions_per_match = int(request.POST.get('questions_per_match', 5))
        max_participants = int(request.POST.get('max_participants', 100))
        difficulty = request.POST.get('difficulty', 'medium')
        bot_enabled = request.POST.get('bot_enabled') == 'on'

        if not title or not start_time or not end_time:
            messages.error(request, 'Sarlavha, boshlanish va tugash vaqti majburiy.')
            return render(request, 'arenas/create.html', {'categories': categories})

        category = get_object_or_404(Category, id=category_id) if category_id else None
        arena = Arena.objects.create(
            title=title,
            description=description,
            category=category,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            questions_per_match=questions_per_match,
            max_participants=max_participants,
            difficulty=difficulty,
            bot_enabled=bot_enabled,
            is_active=True,
            status='upcoming',
        )
        messages.success(request, f'✅ "{arena.title}" arenasi yaratildi!')
        return redirect('arena_detail', arena_id=arena.id)
    return render(request, 'arenas/create.html', {'categories': categories})


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
