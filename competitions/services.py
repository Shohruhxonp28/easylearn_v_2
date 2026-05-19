import random
import math
from django.db import transaction
from django.utils import timezone

from matches.models import Match, DuelQueue
from matches.services import create_match, get_or_create_default_bot
from .models import (
    Arena, ArenaRegistration, ArenaScore,
    Tournament, TournamentParticipant, TournamentRound, TournamentMatch
)


# ─── ARENA SERVICES ───────────────────────────────────────────────────────────

def update_arena_status(arena):
    """Update arena status based on current time"""
    new_status = arena.get_status()
    if arena.status != new_status:
        arena.status = new_status
        arena.save(update_fields=['status'])
    return arena


def get_arena_score(arena, student):
    score, _ = ArenaScore.objects.get_or_create(arena=arena, student=student)
    return score


@transaction.atomic
def start_arena_match(arena, student):
    """
    Find an opponent in the arena or create a bot match.
    Returns (match, status_message)
    """
    from django.db.models import Q

    # Check already in active arena match
    active = Match.objects.filter(
        Q(player1=student) | Q(player2=student),
        status='active',
        match_type='arena'
    ).first()
    if active:
        return active, 'already_in_match'

    # Look for another arena participant waiting
    queue_key = f'arena_{arena.id}'
    # Use DuelQueue as a generic waiting mechanism
    waiting = DuelQueue.objects.filter(
        category=arena.category,
        difficulty='arena_' + str(arena.id)
    ).exclude(student=student).select_for_update().first()

    if waiting:
        opponent = waiting.student
        waiting.delete()
        match = create_match(
            student, opponent,
            arena.category, 'medium', 'arena',
            count=arena.questions_per_match
        )
        return match, 'match_found'
    else:
        # Put in queue for a moment, or go straight to bot
        if arena.bot_enabled:
            bot = get_or_create_default_bot('medium')
            match = create_match(
                student, None,
                arena.category, 'medium', 'arena',
                bot=bot, count=arena.questions_per_match
            )
            return match, 'bot_match'
        else:
            # Add to arena waiting queue
            DuelQueue.objects.get_or_create(
                student=student,
                defaults={
                    'category': arena.category,
                    'difficulty': 'arena_' + str(arena.id)
                }
            )
            return None, 'in_queue'


def update_arena_score(arena, match, student):
    """
    After an arena match finishes, update the student's arena score.
    win=2, draw=1, loss=0
    """
    score = get_arena_score(arena, student)
    score.matches_played += 1

    if match.is_draw:
        score.points += 1
        score.draws += 1
    elif match.winner == student:
        score.points += 2
        score.wins += 1
    else:
        score.losses += 1

    score.save()


# ─── TOURNAMENT SERVICES ──────────────────────────────────────────────────────

@transaction.atomic
def start_tournament(tournament):
    """Create first round bracket for the tournament"""
    if tournament.status != 'registration':
        return False, 'Tournament already started'

    participants = list(
        tournament.participants.filter(is_active=True).select_related('student')
    )

    if len(participants) < 2:
        return False, 'Need at least 2 participants'

    # Shuffle for random bracket
    random.shuffle(participants)

    # If odd number, last player gets BYE
    players = [p.student for p in participants]

    tournament.status = 'active'
    tournament.save()

    create_round(tournament, players, 1)
    return True, 'Tournament started!'


def create_round(tournament, players, round_number):
    """Create a tournament round with given players"""
    t_round = TournamentRound.objects.create(
        tournament=tournament,
        round_number=round_number,
    )

    pairs = []
    player_list = list(players)

    # If odd number, give last player a BYE
    bye_player = None
    if len(player_list) % 2 != 0:
        bye_player = player_list.pop()

    for i in range(0, len(player_list), 2):
        p1 = player_list[i]
        p2 = player_list[i + 1]
        TournamentMatch.objects.create(
            round=t_round,
            player1=p1,
            player2=p2,
            status='pending',
            bracket_position=i // 2
        )

    if bye_player:
        TournamentMatch.objects.create(
            round=t_round,
            player1=bye_player,
            player2=None,
            winner=bye_player,
            status='bye',
            bracket_position=len(player_list) // 2
        )

    return t_round


@transaction.atomic
def start_tournament_match(tournament_match, student):
    """
    Create an actual Match for a TournamentMatch when a player is ready.
    Returns the match.
    """
    if tournament_match.status not in ['pending', 'active']:
        return None, 'Match not available'

    if tournament_match.player1 != student and tournament_match.player2 != student:
        return None, 'Not your match'

    if tournament_match.match:
        return tournament_match.match, 'match_exists'

    if not tournament_match.player2:
        # BYE — auto-win
        tournament_match.winner = student
        tournament_match.status = 'finished'
        tournament_match.save()
        return None, 'bye'

    tournament = tournament_match.round.tournament
    match = create_match(
        tournament_match.player1,
        tournament_match.player2,
        tournament.category,
        'medium',
        'tournament',
        count=5
    )

    if not match:
        return None, 'no_questions'

    tournament_match.match = match
    tournament_match.status = 'active'
    tournament_match.save()
    return match, 'started'


@transaction.atomic
def finalize_tournament_match(tournament_match):
    """After a match finishes, update tournament bracket"""
    if not tournament_match.match or tournament_match.match.status != 'finished':
        return

    match = tournament_match.match
    tournament_match.winner = match.winner
    tournament_match.status = 'finished'
    tournament_match.save()

    # Eliminate loser
    loser = None
    if match.winner == tournament_match.player1:
        loser = tournament_match.player2
    elif match.winner == tournament_match.player2:
        loser = tournament_match.player1

    if loser and not match.is_draw:
        TournamentParticipant.objects.filter(
            tournament=tournament_match.round.tournament,
            student=loser
        ).update(is_eliminated=True)

    # Check if round is complete
    check_round_complete(tournament_match.round)


def check_round_complete(t_round):
    """Check if all matches in round are done, create next round if so"""
    tournament = t_round.tournament
    all_matches = t_round.matches.all()

    for m in all_matches:
        if m.status not in ['finished', 'bye']:
            return False

    t_round.is_complete = True
    t_round.save()

    # Collect winners
    winners = []
    for m in all_matches:
        if m.winner:
            winners.append(m.winner)

    if len(winners) <= 1:
        # Tournament over
        tournament.status = 'finished'
        tournament.save()
        return True

    # Create next round
    next_round_number = t_round.round_number + 1
    create_round(tournament, winners, next_round_number)
    return True


def get_current_round(tournament):
    """Get the current (latest) incomplete round"""
    return tournament.rounds.filter(is_complete=False).order_by('round_number').first()
