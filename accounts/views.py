from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, ProfileForm
from .models import Student
from matches.models import Match


def home(request):
    top_students = Student.objects.order_by('-rating')[:10]
    return render(request, 'home.html', {'top_students': top_students})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    student = request.user
    recent_matches = Match.objects.filter(
        player1=student
    ).union(
        Match.objects.filter(player2=student)
    ).order_by('-ended_at')[:5]

    # Simpler approach to avoid union ordering issues
    from django.db.models import Q
    recent_matches = Match.objects.filter(
        Q(player1=student) | Q(player2=student),
        status='finished'
    ).order_by('-ended_at')[:5]

    return render(request, 'accounts/dashboard.html', {
        'student': student,
        'recent_matches': recent_matches,
    })


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def match_history(request):
    from django.db.models import Q
    student = request.user
    matches = Match.objects.filter(
        Q(player1=student) | Q(player2=student),
        status='finished'
    ).order_by('-ended_at')
    return render(request, 'accounts/match_history.html', {
        'matches': matches,
        'student': student,
    })


def leaderboard(request):
    students = Student.objects.filter(is_staff=False).order_by('-rating')
    return render(request, 'accounts/leaderboard.html', {'students': students})
