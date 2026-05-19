import random
from django.utils import timezone
from apps.matches.models import Match, BotProfile
from apps.matches.services import get_questions_for_match, create_match_questions
from apps.arenas.models import Arena, ArenaParticipant, ArenaScore


def join_arena(arena, user=None, guest=None, display_name=''):
    """Register user/guest as arena participant."""
    if user:
        participant, created = ArenaParticipant.objects.get_or_create(
            arena=arena, user=user,
            defaults={'display_name': display_name or user.full_name or user.username}
        )
    else:
        participant, created = ArenaParticipant.objects.get_or_create(
            arena=arena, guest=guest,
            defaults={'display_name': display_name}
        )

    if created:
        ArenaScore.objects.create(arena=arena, participant=participant)

    return participant


def start_arena_battle(arena, participant):
    """Find opponent or bot, create match."""
    # Check if participant already in active match
    if participant.current_match and participant.current_match.status in ('waiting', 'active'):
        return participant.current_match

    # Find free opponent (different participant, no active match)
    opponents = ArenaParticipant.objects.filter(
        arena=arena,
        is_active=True,
    ).exclude(id=participant.id).filter(
        current_match__isnull=True
    )

    # Exclude bot participants
    if participant.user:
        opponents = opponents.exclude(user__isnull=False, user=participant.user)

    opponent = opponents.order_by('?').first()

    questions = get_questions_for_match(
        arena.category,
        arena.difficulty,
        arena.questions_per_match
    )
    count = len(questions)
    if count == 0:
        return None

    if opponent:
        match = _create_arena_pvp(arena, participant, opponent, questions, count)
    else:
        match = _create_arena_bot(arena, participant, questions, count)

    participant.current_match = match
    participant.save(update_fields=['current_match'])

    return match


def _create_arena_pvp(arena, p1, p2, questions, count):
    match = Match.objects.create(
        match_type='arena',
        status='active',
        player1=p1.user,
        player2=p2.user,
        guest_player=p1.guest if not p1.user else None,
        arena=arena,
        category=arena.category,
        total_questions=count,
        started_at=timezone.now(),
    )
    create_match_questions(match, questions)

    p2.current_match = match
    p2.save(update_fields=['current_match'])
    return match


def _create_arena_bot(arena, participant, questions, count):
    bot = BotProfile.objects.filter(level=arena.difficulty).first()
    if not bot:
        bot = BotProfile.objects.first()
    if not bot:
        bot = BotProfile.objects.create(name='ArenaBot', level='medium', avatar_initial='AB')

    match = Match.objects.create(
        match_type='arena',
        status='active',
        player1=participant.user,
        guest_player=participant.guest if not participant.user else None,
        bot=bot,
        arena=arena,
        category=arena.category,
        total_questions=count,
        started_at=timezone.now(),
    )
    create_match_questions(match, questions)
    return match
