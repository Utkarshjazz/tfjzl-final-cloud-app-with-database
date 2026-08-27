from django.contrib import admin

# Import all required models
from .models import (
    Course,
    Lesson,
    Instructor,
    Learner,
    Question,
    Choice,
    Submission
)


# Choice inline
class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 2


# Question inline
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


# Lesson inline
class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5


# Question Admin
class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ('question_text', 'course', 'grade')
    list_filter = ['course']
    search_fields = ['question_text']


# Course Admin
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline, QuestionInline]
    list_display = ('name', 'pub_date')
    list_filter = ['pub_date']
    search_fields = ['name', 'description']


# Lesson Admin
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title']


# Submission Admin
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('enrollment',)
    filter_horizontal = ('choices',)


# Register models
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Submission, SubmissionAdmin)
