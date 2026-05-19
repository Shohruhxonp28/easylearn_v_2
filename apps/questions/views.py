from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Category, Question, QuestionOption


def staff_required(view_func):
    """Custom decorator: faqat staff/superuser uchun."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Bu sahifaga kirish huquqingiz yo\'q.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@staff_required
def question_create(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        # Asosiy savol ma'lumotlari
        category_id = request.POST.get('category')
        title = request.POST.get('title', '').strip()
        body = request.POST.get('body', '').strip()
        question_type = request.POST.get('question_type', 'single')
        difficulty = request.POST.get('difficulty', 'medium')
        points = int(request.POST.get('points', 10))
        explanation = request.POST.get('explanation', '').strip()
        status = request.POST.get('status', 'draft')

        if not title or not body or not category_id:
            messages.error(request, 'Kategoriya, sarlavha va savol matni majburiy.')
            return render(request, 'questions/create.html', {'categories': categories})

        category = get_object_or_404(Category, id=category_id)
        question = Question.objects.create(
            category=category,
            title=title,
            body=body,
            question_type=question_type,
            difficulty=difficulty,
            points=points,
            explanation=explanation,
            status=status,
        )

        # Variantlarni saqlash (option_text_1 ... option_text_6)
        has_correct = False
        for i in range(1, 7):
            text = request.POST.get(f'option_text_{i}', '').strip()
            if text:
                is_correct = request.POST.get(f'option_correct_{i}') == 'on'
                if is_correct:
                    has_correct = True
                QuestionOption.objects.create(
                    question=question,
                    text=text,
                    is_correct=is_correct,
                    order=i,
                )

        if not has_correct:
            messages.warning(request, 'Kamida bitta to\'g\'ri javob bo\'lishi kerak!')

        messages.success(request, f'✅ "{question.title}" savoli yaratildi!')
        return redirect('question_create')

    return render(request, 'questions/create.html', {'categories': categories})


@login_required
@staff_required
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '📚').strip()
        if name:
            cat, created = Category.objects.get_or_create(name=name, defaults={'description': description, 'icon': icon})
            if created:
                messages.success(request, f'✅ "{name}" kategoriyasi yaratildi!')
            else:
                messages.warning(request, f'"{name}" kategoriyasi allaqachon mavjud.')
        return redirect('question_create')
    return redirect('question_create')
