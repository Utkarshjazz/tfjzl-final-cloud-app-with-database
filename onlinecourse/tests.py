from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Choice, Course, Enrollment, Instructor, Question, Submission


class AssessmentFlowTests(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            username='learner', password='safe-test-password'
        )
        self.other_user = User.objects.create_user(
            username='other', password='safe-test-password'
        )
        self.instructor_user = User.objects.create_user(
            username='instructor', password='safe-test-password'
        )
        self.instructor = Instructor.objects.create(
            user=self.instructor_user, full_time=True, total_learners=10
        )
        self.course = Course.objects.create(
            name='Learning Django',
            image='course_images/django.png',
            description='Learn the Django web framework.',
            pub_date=date.today(),
        )
        self.course.instructors.add(self.instructor)
        self.enrollment = Enrollment.objects.create(
            user=self.learner, course=self.course, mode='honor'
        )
        self.question = Question.objects.create(
            course=self.course,
            question_text='Which choices are correct?',
            grade=100,
        )
        self.correct_yes = Choice.objects.create(
            question=self.question, choice_text='Yes', is_correct=True
        )
        self.correct_also = Choice.objects.create(
            question=self.question, choice_text='Also yes', is_correct=True
        )
        self.incorrect = Choice.objects.create(
            question=self.question, choice_text='No', is_correct=False
        )

    def test_enrolled_learner_can_submit_and_view_a_passing_result(self):
        self.client.force_login(self.learner)
        response = self.client.post(
            reverse('onlinecourse:submit', args=[self.course.id]),
            {
                f'choice_{self.question.id}': [
                    str(self.correct_yes.id), str(self.correct_also.id)
                ]
            },
        )

        submission = Submission.objects.get(enrollment=self.enrollment)
        self.assertRedirects(
            response,
            reverse(
                'onlinecourse:show_exam_result',
                args=[self.course.id, submission.id],
            ),
        )
        self.assertSetEqual(
            set(submission.choices.all()),
            {self.correct_yes, self.correct_also},
        )

        result = self.client.get(
            reverse(
                'onlinecourse:show_exam_result',
                args=[self.course.id, submission.id],
            )
        )
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, 'Congratulations')
        self.assertContains(result, '100%')
        self.assertContains(result, 'Which choices are correct?')

    def test_question_requires_the_complete_correct_choice_set(self):
        self.client.force_login(self.learner)
        response = self.client.post(
            reverse('onlinecourse:submit', args=[self.course.id]),
            {f'choice_{self.question.id}': str(self.correct_yes.id)},
        )
        submission = Submission.objects.get(enrollment=self.enrollment)
        self.assertRedirects(
            response,
            reverse(
                'onlinecourse:show_exam_result',
                args=[self.course.id, submission.id],
            ),
        )
        result = self.client.get(
            reverse(
                'onlinecourse:show_exam_result',
                args=[self.course.id, submission.id],
            )
        )
        self.assertContains(result, '0%')
        self.assertContains(result, 'Keep learning and try again')

    def test_submission_cannot_include_a_choice_from_another_course(self):
        other_course = Course.objects.create(
            name='Other course',
            image='course_images/django.png',
            description='Another course.',
            pub_date=date.today(),
        )
        other_question = Question.objects.create(
            course=other_course, question_text='Other question', grade=100
        )
        foreign_choice = Choice.objects.create(
            question=other_question, choice_text='Foreign', is_correct=True
        )
        self.client.force_login(self.learner)
        self.client.post(
            reverse('onlinecourse:submit', args=[self.course.id]),
            {f'choice_{self.question.id}': str(foreign_choice.id)},
        )
        submission = Submission.objects.get(enrollment=self.enrollment)
        self.assertFalse(submission.choices.exists())

    def test_another_learner_cannot_read_a_submission(self):
        submission = Submission.objects.create(enrollment=self.enrollment)
        self.client.force_login(self.other_user)
        response = self.client.get(
            reverse(
                'onlinecourse:show_exam_result',
                args=[self.course.id, submission.id],
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_course_page_displays_exam_for_an_enrolled_learner(self):
        self.client.force_login(self.learner)
        response = self.client.get(
            reverse('onlinecourse:course_details', args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Course assessment')
        self.assertContains(response, 'Which choices are correct?')
