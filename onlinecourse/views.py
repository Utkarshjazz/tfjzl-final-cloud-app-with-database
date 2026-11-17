from django.shortcuts import render
from django.http import HttpResponseRedirect
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.

def registration_request(request):
    context = {}

    if request.method == 'GET':
        return render(
            request,
            'onlinecourse/user_registration_bootstrap.html',
            context
        )

    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']

        user_exist = False

        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")

        if not user_exist:
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password
            )

            login(request, user)

            return redirect("onlinecourse:index")

        else:
            context['message'] = "User already exists."

            return render(
                request,
                'onlinecourse/user_registration_bootstrap.html',
                context
            )


def login_request(request):
    context = {}

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']

        user = authenticate(
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            return redirect('onlinecourse:index')

        else:
            context['message'] = "Invalid username or password."

            return render(
                request,
                'onlinecourse/user_login_bootstrap.html',
                context
            )

    else:
        return render(
            request,
            'onlinecourse/user_login_bootstrap.html',
            context
        )


def logout_request(request):
    logout(request)

    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False

    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(
            user=user,
            course=course
        ).count()

        if num_results > 0:
            is_enrolled = True

    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user

        courses = Course.objects.order_by(
            '-total_enrollment'
        )[:10]

        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(
                    user,
                    course
                )

        return courses


# CourseDetailView
class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_details_bootstrap.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = context['course']
        context['questions'] = Question.objects.filter(
            course=course
        ).prefetch_related('choice_set').order_by('id')
        context['is_enrolled'] = (
            self.request.user.is_authenticated and
            check_if_enrolled(self.request.user, course)
        )
        return context


def enroll(request, course_id):
    course = get_object_or_404(
        Course,
        pk=course_id
    )

    user = request.user

    is_enrolled = check_if_enrolled(
        user,
        course
    )

    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(
            user=user,
            course=course,
            mode='honor'
        )

        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(
        reverse(
            viewname='onlinecourse:course_details',
            args=(course.id,)
        )
    )


# Submit exam
@login_required
@require_POST
def submit(request, course_id):
    """
    Create an exam submission for the enrolled user,
    collect the selected choices, and redirect to
    the exam result page.
    """

    course = get_object_or_404(
        Course,
        pk=course_id
    )

    user = request.user

    # Get the enrollment for this user and course
    enrollment = get_object_or_404(
        Enrollment,
        user=user,
        course=course
    )

    # Create a new submission
    selected_ids = extract_answers(request)
    submission = Submission.objects.create(enrollment=enrollment)
    valid_choices = Choice.objects.filter(
        pk__in=selected_ids,
        question__course=course
    )
    submission.choices.set(valid_choices)

    # Redirect to exam result
    return redirect(
        'onlinecourse:show_exam_result',
        course_id=course.id,
        submission_id=submission.id
    )


# Extract answers from exam form
def extract_answers(request):
    submitted_answers = set()

    for key in request.POST:
        if key.startswith('choice'):
            for value in request.POST.getlist(key):
                try:
                    submitted_answers.add(int(value))
                except (TypeError, ValueError):
                    logger.warning("Ignoring invalid choice value: %s", value)

    return submitted_answers


# Show exam result
@login_required
def show_exam_result(request, course_id, submission_id):
    """
    Display the exam result, calculate the learner's
    score, and show the result for each question.
    """

    course = get_object_or_404(
        Course,
        pk=course_id
    )

    submission = get_object_or_404(
        Submission,
        pk=submission_id,
        enrollment__user=request.user,
        enrollment__course=course
    )

    selected_ids = set(
        submission.choices.values_list('id', flat=True)
    )
    questions = Question.objects.filter(
        course=course
    ).prefetch_related('choice_set').order_by('id')

    raw_score = 0
    total_grade = sum(question.grade for question in questions)
    question_results = []

    for question in questions:
        choices = list(question.choice_set.all())
        selected_for_question = {
            choice.id for choice in choices if choice.id in selected_ids
        }
        correct = question.is_get_score(selected_for_question)
        if correct:
            raw_score += question.grade
        question_results.append({
            'question': question,
            'choices': [
                {
                    'choice': choice,
                    'selected': choice.id in selected_for_question,
                    'is_correct': choice.is_correct,
                }
                for choice in choices
            ],
            'is_correct': correct,
        })

    grade = round(raw_score * 100 / total_grade, 2) if total_grade else 0
    passed = grade > 80

    context = {
        'course': course,
        'submission': submission,
        'selected_choices': submission.choices.all(),
        'question_results': question_results,
        'questions': questions,
        'grade': grade,
        'score': raw_score,
        'total_grade': total_grade,
        'passed': passed,
    }

    return render(
        request,
        'onlinecourse/exam_result_bootstrap.html',
        context
    )
