from django.utils import timezone
from apps.matches.models import Match, BotProfile
from apps.matches.services import get_questions_for_match, create_match_questions
from apps.duels.models import DuelQueue


def find_or_create_duel(player, category=None, difficulty=None):
    """Main entry point: find opponent or create bot match."""
    # Check if player already in active match
    active = Match.objects.filter(
        status__in=['waiting', 'active'],
        match_type='duel',
        player1=player,
    ).first() or Match.objects.filter(
        status__in=['waiting', 'active'],
        match_type='duel',
        player2=player,
    ).first()
    if active:
        return active

    # Try to find waiting player in queue
    queue_entry = DuelQueue.objects.exclude(player=player).filter(
        category=category
    ).order_by('joined_at').first()

    if queue_entry:
        opponent = queue_entry.player
        queue_entry.delete()
        # Remove self from queue too if present
        DuelQueue.objects.filter(player=player).delete()
        return _create_pvp_match(player, opponent, category, difficulty)
    else:
        # Add to queue and immediately create bot match
        DuelQueue.objects.filter(player=player).delete()
        return _create_bot_match(player, category, difficulty)


def _create_pvp_match(player1, player2, category, difficulty):
    questions = get_questions_for_match(category, difficulty, count=5)
    match = Match.objects.create(
        match_type='duel',
        status='active',
        player1=player1,
        player2=player2,
        category=category,
        difficulty=difficulty or '',
        total_questions=len(questions),
        started_at=timezone.now(),
    )
    create_match_questions(match, questions)
    return match


def _create_bot_match(player, category, difficulty):
    bot = BotProfile.objects.filter(level=difficulty or 'medium').first()
    if not bot:
        bot = BotProfile.objects.first()
    if not bot:
        bot = BotProfile.objects.create(name='QuizBot', level='medium', avatar_initial='QB')

    questions = get_questions_for_match(category, difficulty, count=5)
    count = len(questions)
    if count == 0:
        count = 1

    match = Match.objects.create(
        match_type='duel',
        status='active',
        player1=player,
        bot=bot,
        category=category,
        difficulty=difficulty or '',
        total_questions=count,
        started_at=timezone.now(),
    )
    if questions:
        create_match_questions(match, questions)
    return match
