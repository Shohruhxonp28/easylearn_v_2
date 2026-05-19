from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from apps.accounts.models import User
from apps.matches.models import Match


def home(request):
    recent_matches = Match.objects.filter(status='finished').select_related(
        'player1', 'player2', 'bot', 'category'
    ).order_by('-ended_at')[:6]
    top_players = User.objects.order_by('-rating')[:10]
    return render(request, 'home.html', {
        'recent_matches': recent_matches,
        'top_players': top_players,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username or not full_name or not password1:
            messages.error(request, 'All fields are required.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(
                username=username,
                full_name=full_name,
                password=password1,
            )
            login(request, user)
            messages.success(request, f'Welcome, {full_name}!')
            return redirect('dashboard')
    return render(request, 'accounts/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        messages.error(request, 'Invalid credentials.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    user = request.user
    recent = Match.objects.filter(
        Q(player1=user) | Q(player2=user),
        status='finished'
    ).select_related('player1', 'player2', 'bot', 'category').order_by('-ended_at')[:5]

    return render(request, 'accounts/dashboard.html', {
        'user': user,
        'recent_matches': recent,
    })


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        if full_name:
            user.full_name = full_name
            user.save()
            messages.success(request, 'Profile updated.')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'profile_user': user})


@login_required
def match_history(request):
    user = request.user
    matches = Match.objects.filter(
        Q(player1=user) | Q(player2=user),
        status='finished'
    ).select_related('player1', 'player2', 'bot', 'category').order_by('-ended_at')
    return render(request, 'accounts/match_history.html', {'matches': matches})
