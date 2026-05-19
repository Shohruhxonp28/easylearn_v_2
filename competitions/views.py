from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Arena, ArenaRegistration, ArenaScore, Tournament, TournamentParticipant, TournamentMatch, TournamentRound
from .services import (
    update_arena_status, start_arena_match, update_arena_score,
    start_tournament, start_tournament_match, finalize_tournament_match,
    get_current_round
)
from matches.models import Match
from matches.services import submit_answer_and_advance, maybe_finalize, finalize_match


# ─── ARENA ────────────────────────────────────────────────────────────────────

@login_required
def arena_list(request):
    arenas = Arena.objects.all().order_by('-start_time')
    for arena in arenas:
        update_arena_status(arena)
    student = request.user
    registered_ids = set(ArenaRegistration.objects.filter(student=student).values_list('arena_id', flat=True))
    return render(request, 'competitions/arena_list.html', {'arenas': arenas, 'registered_ids': registered_ids})


@login_required
def arena_detail(request, arena_id):
    arena = get_object_or_404(Arena, id=arena_id)
    update_arena_status(arena)
    student = request.user
    is_registered = ArenaRegistration.objects.filter(arena=arena, student=student).exists()
    active_match = Match.objects.filter(Q(player1=student)|Q(player2=student), status='active', match_type='arena').first()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'register' and not is_registered:
            ArenaRegistration.objects.create(arena=arena, student=student)
            messages.success(request, f'Registered for {arena.title}!')
            return redirect('arena_detail', arena_id=arena.id)
        elif action == 'start_battle' and is_registered and arena.is_live():
            match, status = start_arena_match(arena, student)
            if status == 'already_in_match' and active_match:
                return redirect('arena_match_play', match_id=active_match.id, arena_id=arena.id)
            elif match:
                return redirect('arena_match_play', match_id=match.id, arena_id=arena.id)
            elif status == 'in_queue':
                messages.info(request, 'Waiting for opponent...')
            return redirect('arena_detail', arena_id=arena.id)

    scores = ArenaScore.objects.filter(arena=arena).order_by('-points').select_related('student')[:20]
    return render(request, 'competitions/arena_detail.html', {
        'arena': arena, 'is_registered': is_registered, 'active_match': active_match, 'scores': scores,
    })


@login_required
def arena_match_play(request, arena_id, match_id):
    arena = get_object_or_404(Arena, id=arena_id)
    match = get_object_or_404(Match, id=match_id)
    student = request.user

    if match.player1 != student and match.player2 != student:
        messages.error(request, 'Access denied.')
        return redirect('arena_detail', arena_id=arena.id)

    if match.status == 'finished':
        return redirect('arena_match_result', match_id=match.id, arena_id=arena.id)

    is_p1 = match.player1 == student
    current_idx = match.player1_current_index if is_p1 else match.player2_current_index
    total = match.total_questions()

    if current_idx >= total:
        if maybe_finalize(match):
            update_arena_score(arena, match, student)
            return redirect('arena_match_result', match_id=match.id, arena_id=arena.id)
        return render(request, 'matches/match_waiting.html', {
            'match': match, 'opponent_name': match.get_opponent_name(student), 'total': total,
        })

    qs_list = list(match.questions.order_by('order'))
    current_mq = qs_list[current_idx]

    if request.method == 'POST':
        answer = request.POST.get('answer', '').strip().upper()
        if answer not in ['A','B','C','D']:
            messages.error(request, 'Select an answer.')
            return redirect('arena_match_play', arena_id=arena_id, match_id=match_id)
        success, player_done, msg = submit_answer_and_advance(match, student, current_idx, answer)
        if player_done or (success and maybe_finalize(match)):
            match.refresh_from_db()
            if match.status == 'finished':
                update_arena_score(arena, match, student)
                return redirect('arena_match_result', match_id=match.id, arena_id=arena.id)
        return redirect('arena_match_play', arena_id=arena_id, match_id=match_id)

    answered = []
    for i, mq in enumerate(qs_list):
        if i < current_idx:
            correct = mq.is_player1_correct() if is_p1 else mq.is_player2_correct()
            answered.append({'n':i+1,'done':True,'correct':correct})
        elif i == current_idx:
            answered.append({'n':i+1,'done':False,'current':True})
        else:
            answered.append({'n':i+1,'done':False})

    my_score = sum(mq.question.points for i,mq in enumerate(qs_list) if i<current_idx and (mq.is_player1_correct() if is_p1 else mq.is_player2_correct()))
    diff_colors = {'easy':'success','medium':'warning','hard':'danger'}

    return render(request, 'competitions/arena_match_play.html', {
        'match': match, 'arena': arena,
        'current_mq': current_mq, 'question': current_mq.question, 'options': current_mq.question.get_options(),
        'current_idx': current_idx, 'total': total, 'answered': answered, 'my_score': my_score,
        'opponent_name': match.get_opponent_name(student), 'is_p1': is_p1,
        'diff_color': diff_colors.get(match.difficulty,'secondary'),
    })


@login_required
def arena_match_result(request, arena_id, match_id):
    arena = get_object_or_404(Arena, id=arena_id)
    match = get_object_or_404(Match, id=match_id)
    student = request.user
    if match.status != 'finished':
        finalize_match(match)
        match.refresh_from_db()
        update_arena_score(arena, match, student)

    is_p1 = match.player1 == student
    my_score = match.player1_score if is_p1 else match.player2_score
    opp_score = match.player2_score if is_p1 else match.player1_score

    if match.is_draw: result, arena_pts = 'draw', 1
    elif match.winner == student: result, arena_pts = 'win', 2
    else: result, arena_pts = 'loss', 0

    return render(request, 'competitions/arena_match_result.html', {
        'match': match, 'arena': arena, 'my_score': my_score, 'opp_score': opp_score,
        'result': result, 'arena_pts': arena_pts, 'opponent_name': match.get_opponent_name(student),
    })


@login_required
def arena_leaderboard(request, arena_id):
    arena = get_object_or_404(Arena, id=arena_id)
    scores = ArenaScore.objects.filter(arena=arena).order_by('-points', '-wins').select_related('student')
    return render(request, 'competitions/arena_leaderboard.html', {'arena': arena, 'scores': scores})


# ─── TOURNAMENT ───────────────────────────────────────────────────────────────

@login_required
def tournament_list(request):
    from questions.models import Category
    tournaments = Tournament.objects.all().order_by('-start_time')
    student = request.user
    registered_ids = set(TournamentParticipant.objects.filter(student=student).values_list('tournament_id', flat=True))
    categories = Category.objects.all()
    return render(request, 'competitions/tournament_list.html', {
        'tournaments': tournaments, 
        'registered_ids': registered_ids,
        'categories': categories,
    })


@login_required
def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    student = request.user
    participant = TournamentParticipant.objects.filter(tournament=tournament, student=student).first()
    is_registered = participant is not None

    if request.method == 'POST' and request.POST.get('action') == 'register':
        if tournament.status != 'registration':
            messages.error(request, 'Registration is closed.')
        elif tournament.is_full():
            messages.error(request, 'Tournament is full.')
        elif not is_registered:
            TournamentParticipant.objects.create(tournament=tournament, student=student)
            messages.success(request, 'Registered!')
            is_registered = True
            participant = TournamentParticipant.objects.get(tournament=tournament, student=student)
        return redirect('tournament_detail', tournament_id=tournament.id)

    current_round = get_current_round(tournament)
    my_match = None
    if current_round and is_registered:
        my_match = TournamentMatch.objects.filter(round=current_round).filter(Q(player1=student)|Q(player2=student)).first()
    participants = tournament.participants.filter(is_active=True).select_related('student').order_by('registered_at')
    return render(request, 'competitions/tournament_detail.html', {
        'tournament': tournament, 'participant': participant, 'is_registered': is_registered,
        'current_round': current_round, 'my_match': my_match, 'participants': participants,
    })


@login_required
def tournament_bracket(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    rounds = tournament.rounds.prefetch_related('matches__player1','matches__player2','matches__winner').all()
    return render(request, 'competitions/tournament_bracket.html', {'tournament': tournament, 'rounds': rounds})


@login_required
def play_tournament_match(request, tournament_id, tmatch_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    t_match = get_object_or_404(TournamentMatch, id=tmatch_id)
    student = request.user

    if t_match.player1 != student and t_match.player2 != student:
        messages.error(request, 'Not your match.')
        return redirect('tournament_detail', tournament_id=tournament.id)
    if t_match.status == 'bye':
        messages.info(request, 'You have a BYE — you advance automatically!')
        return redirect('tournament_detail', tournament_id=tournament.id)
    if t_match.status == 'finished':
        return redirect('tournament_match_result', tournament_id=tournament.id, tmatch_id=t_match.id)

    match, status = start_tournament_match(t_match, student)
    if status == 'no_questions':
        messages.error(request, 'No questions available.')
        return redirect('tournament_detail', tournament_id=tournament.id)
    if status == 'bye':
        messages.success(request, 'You advance with a BYE!')
        return redirect('tournament_detail', tournament_id=tournament.id)
    if not match:
        return redirect('tournament_detail', tournament_id=tournament.id)

    is_p1 = match.player1 == student
    current_idx = match.player1_current_index if is_p1 else match.player2_current_index
    total = match.total_questions()

    if current_idx >= total:
        if maybe_finalize(match):
            finalize_tournament_match(t_match)
            return redirect('tournament_match_result', tournament_id=tournament.id, tmatch_id=t_match.id)
        return render(request, 'matches/match_waiting.html', {
            'match': match, 'opponent_name': match.get_opponent_name(student), 'total': total,
        })

    qs_list = list(match.questions.order_by('order'))
    current_mq = qs_list[current_idx]

    if request.method == 'POST':
        answer = request.POST.get('answer','').strip().upper()
        if answer not in ['A','B','C','D']:
            messages.error(request, 'Select an answer.')
            return redirect('play_tournament_match', tournament_id=tournament.id, tmatch_id=t_match.id)
        success, player_done, msg = submit_answer_and_advance(match, student, current_idx, answer)
        if player_done or (success and maybe_finalize(match)):
            match.refresh_from_db()
            if match.status == 'finished':
                finalize_tournament_match(t_match)
                return redirect('tournament_match_result', tournament_id=tournament.id, tmatch_id=t_match.id)
        return redirect('play_tournament_match', tournament_id=tournament.id, tmatch_id=t_match.id)

    answered = []
    for i, mq in enumerate(qs_list):
        if i < current_idx:
            correct = mq.is_player1_correct() if is_p1 else mq.is_player2_correct()
            answered.append({'n':i+1,'done':True,'correct':correct})
        elif i == current_idx:
            answered.append({'n':i+1,'done':False,'current':True})
        else:
            answered.append({'n':i+1,'done':False})

    my_score = sum(mq.question.points for i,mq in enumerate(qs_list) if i<current_idx and (mq.is_player1_correct() if is_p1 else mq.is_player2_correct()))
    diff_colors = {'easy':'success','medium':'warning','hard':'danger'}

    return render(request, 'competitions/tournament_match_play.html', {
        'tournament': tournament, 't_match': t_match, 'match': match,
        'current_mq': current_mq, 'question': current_mq.question, 'options': current_mq.question.get_options(),
        'current_idx': current_idx, 'total': total, 'answered': answered, 'my_score': my_score,
        'opponent_name': match.get_opponent_name(student), 'is_p1': is_p1,
        'diff_color': diff_colors.get(match.difficulty,'secondary'),
    })


@login_required
def tournament_match_result(request, tournament_id, tmatch_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    t_match = get_object_or_404(TournamentMatch, id=tmatch_id)
    student = request.user
    match = t_match.match

    if match:
        is_p1 = match.player1 == student
        my_score = match.player1_score if is_p1 else match.player2_score
        opp_score = match.player2_score if is_p1 else match.player1_score
        opponent_name = match.get_opponent_name(student)
        advanced = t_match.winner == student
    else:
        my_score = opp_score = 0
        opponent_name = 'BYE'
        advanced = True

    return render(request, 'competitions/tournament_match_result.html', {
        'tournament': tournament, 't_match': t_match, 'match': match,
        'my_score': my_score, 'opp_score': opp_score, 'opponent_name': opponent_name, 'advanced': advanced,
    })


from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    from questions.models import Category, Question
    from .models import Tournament, Arena
    
    categories = Category.objects.all()
    tournaments = Tournament.objects.all().order_by('-start_time')
    arenas = Arena.objects.all().order_by('-start_time')
    questions = Question.objects.all().order_by('-created_at')[:40]
    
    return render(request, 'competitions/admin_dashboard.html', {
        'categories': categories,
        'tournaments': tournaments,
        'arenas': arenas,
        'questions': questions,
    })


@user_passes_test(lambda u: u.is_staff)
def admin_create_question(request):
    if request.method == 'POST':
        from questions.models import Category, Question, QuestionOption
        category_id = request.POST.get('category')
        title = request.POST.get('title')
        body = request.POST.get('body')
        difficulty = request.POST.get('difficulty')
        points = int(request.POST.get('points', 10))
        correct_answer = request.POST.get('correct_answer')
        explanation = request.POST.get('explanation', '')
        
        opt_a = request.POST.get('option_a')
        opt_b = request.POST.get('option_b')
        opt_c = request.POST.get('option_c')
        opt_d = request.POST.get('option_d')
        
        if not (category_id and title and body and correct_answer and opt_a and opt_b and opt_c and opt_d):
            messages.error(request, "Iltimos, barcha majburiy maydonlarni to'ldiring!")
            return redirect('admin_dashboard')
            
        category = get_object_or_404(Category, id=category_id)
        
        # Create Question
        q = Question.objects.create(
            category=category,
            title=title,
            body=body,
            difficulty=difficulty,
            points=points,
            correct_answer=correct_answer,
            explanation=explanation,
            status='published'
        )
        
        # Create Question Options
        QuestionOption.objects.create(question=q, label='A', text=opt_a)
        QuestionOption.objects.create(question=q, label='B', text=opt_b)
        QuestionOption.objects.create(question=q, label='C', text=opt_c)
        QuestionOption.objects.create(question=q, label='D', text=opt_d)
        
        messages.success(request, f"'{title}' nomli yangi savol muvaffaqiyatli yaratildi va chop etildi!")
    return redirect('admin_dashboard')


@user_passes_test(lambda u: u.is_staff)
def admin_create_tournament(request):
    if request.method == 'POST':
        from questions.models import Category
        from .models import Tournament
        
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        start_time_str = request.POST.get('start_time')
        max_participants = int(request.POST.get('max_participants', 8))
        description = request.POST.get('description', '')
        
        if not (title and category_id and start_time_str):
            messages.error(request, "Iltimos, barcha majburiy maydonlarni to'ldiring!")
            return redirect('admin_dashboard')
            
        category = get_object_or_404(Category, id=category_id)
        
        # Parse timezone-aware start time
        from django.utils.dateparse import parse_datetime
        from django.utils.timezone import make_aware
        
        naive_dt = parse_datetime(start_time_str)
        if naive_dt:
            if timezone.is_naive(naive_dt):
                start_time = make_aware(naive_dt)
            else:
                start_time = naive_dt
        else:
            messages.error(request, "Noto'g'ri sana formati kiritildi!")
            return redirect('admin_dashboard')
            
        Tournament.objects.create(
            title=title,
            category=category,
            start_time=start_time,
            max_participants=max_participants,
            description=description,
            status='registration'
        )
        
        messages.success(request, f"'{title}' nomli yangi turnir yaratildi va ro'yxatga olish ochildi!")
    return redirect('admin_dashboard')


@user_passes_test(lambda u: u.is_staff)
def admin_start_tournament(request, tournament_id):
    from .models import Tournament
    from .services import start_tournament
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    success, msg = start_tournament(tournament)
    if success:
        messages.success(request, f"{tournament.title}: {msg}")
    else:
        messages.error(request, f"{tournament.title}: {msg}")
    return redirect('admin_dashboard')

