from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = 'onlinecourse'

urlpatterns = [
    # Home page
    path(
        route='',
        view=views.CourseListView.as_view(),
        name='index'
    ),

    # User registration
    path(
        'registration/',
        views.registration_request,
        name='registration'
    ),

    # User login
    path(
        'login/',
        views.login_request,
        name='login'
    ),

    # User logout
    path(
        'logout/',
        views.logout_request,
        name='logout'
    ),

    # Course details
    # Example: /onlinecourse/5/
    path(
        '<int:pk>/',
        views.CourseDetailView.as_view(),
        name='course_details'
    ),

    # Enroll in course
    # Example: /onlinecourse/5/enroll/
    path(
        '<int:course_id>/enroll/',
        views.enroll,
        name='enroll'
    ),

    # Submit exam
    # Example: /onlinecourse/5/submit/
    path(
        '<int:course_id>/submit/',
        views.submit,
        name='submit'
    ),

    # Show exam result
    # Example: /onlinecourse/5/exam_result/10/
    path(
        '<int:course_id>/exam_result/<int:submission_id>/',
        views.show_exam_result,
        name='show_exam_result'
    ),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
