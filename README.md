# Online Course App: Assessment Feature

This Django app extends the starter online course site with course questions, multiple-select choices, learner submissions, and scored assessment results.

## Run in the Skills Network lab

```sh
pip install -r requirements.txt
python3 manage.py makemigrations onlinecourse
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

Open `/admin/` to add an instructor, course, lessons, questions, and choices. Sign in as a learner, enroll in the course, then submit the assessment from the course details page. Each submission is stored against its enrollment, and only that learner can view its result.

## Assessment behavior

- A question may have several correct choices.
- A learner earns the question's points only when every correct choice and no incorrect choice is selected.
- The result page shows the percentage, point total, selected answers, and correct answers. Scores above 80% pass.
- Learners may retake the assessment; each attempt creates a separate submission.

## Project layout

- `onlinecourse/models.py`: question, choice, and submission data models
- `onlinecourse/admin.py`: course, question, lesson, choice, and submission admin forms
- `onlinecourse/templates/onlinecourse/course_details_bootstrap.html`: course detail page and exam form
- `onlinecourse/views.py` and `onlinecourse/urls.py`: submission and result flow
- `onlinecourse/templates/onlinecourse/exam_result_bootstrap.html`: scored result and answer review

The project uses SQLite by default. The existing ER diagram is available under `static/media/course_images/onlinecourse_app_er.png`.
