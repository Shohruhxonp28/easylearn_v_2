from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.questions.models import Category
from apps.matches.models import Match
from apps.duels.services import find_or_create_duel


@login_required
def duel_lobby(request):
    categories = Category.objects.all()
    return render(request, 'duels/lobby.html', {'categories': categories})


@login_required
def start_duel(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        difficulty = request.POST.get('difficulty', '')
        category = None
        if category_id:
            category = Category.objects.filter(id=category_id).first()

        match = find_or_create_duel(request.user, category, difficulty)
        if match.total_questions == 0:
            messages.warning(request, 'No questions available for this category/difficulty. Try another.')
            return redirect('duel_lobby')
        return redirect('match_play', match_id=match.id)
    return redirect('duel_lobby')
