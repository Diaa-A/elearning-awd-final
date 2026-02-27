"""
Views for the courses application.

Handles course listing, creation, editing, enrollment, material upload,
student management (block/remove), and feedback submission.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .forms import CourseMaterialForm, CourseForm, FeedbackForm
from .models import Course, CourseMaterial, Enrollment, Feedback


class CourseListView(LoginRequiredMixin, View):
    """
    Display a list of all available courses.

    Requirement R1(e): Students should see a list of available courses
    and select the courses they want to enrol to.
    """

    def get(self, request):
        """List all active courses with optional search filtering."""
        query = request.GET.get('q', '').strip()
        courses = Course.objects.filter(is_active=True).select_related('teacher')

        if query:
            courses = courses.filter(
                title__icontains=query
            ) | courses.filter(
                code__icontains=query
            ) | courses.filter(
                category__icontains=query
            )

        # Track which courses the current student is enrolled in
        enrolled_course_ids = []
        if request.user.is_student:
            enrolled_course_ids = list(
                Enrollment.objects.filter(
                    student=request.user,
                    status=Enrollment.Status.ACTIVE,
                ).values_list('course_id', flat=True)
            )

        context = {
            'courses': courses,
            'query': query,
            'enrolled_course_ids': enrolled_course_ids,
        }
        return render(request, 'courses/course_list.html', context)


class CourseDetailView(LoginRequiredMixin, View):
    """
    Display a course's detail page with materials and feedback.

    Shows course information, uploaded materials (accessible to enrolled
    students and the teacher), and student feedback.
    """

    def get(self, request, pk):
        """Display the course detail page."""
        course = get_object_or_404(
            Course.objects.select_related('teacher'), pk=pk,
        )
        materials = course.materials.all()
        feedbacks = course.feedbacks.select_related('student').all()

        # Check enrollment status for students
        is_enrolled = False
        enrollment = None
        if request.user.is_student:
            enrollment = Enrollment.objects.filter(
                student=request.user,
                course=course,
            ).first()
            is_enrolled = enrollment and enrollment.status == Enrollment.Status.ACTIVE

        # Check if the student has already left feedback
        has_feedback = Feedback.objects.filter(
            student=request.user, course=course,
        ).exists() if request.user.is_student else False

        context = {
            'course': course,
            'materials': materials,
            'feedbacks': feedbacks,
            'is_enrolled': is_enrolled,
            'enrollment': enrollment,
            'has_feedback': has_feedback,
            'is_teacher': course.teacher == request.user,
        }
        return render(request, 'courses/course_detail.html', context)


class CourseCreateView(LoginRequiredMixin, View):
    """
    Create a new course.

    Requirement R1(d): Teachers should be able to create courses.
    Only users with the teacher role can access this view.
    """

    def get(self, request):
        """Display the course creation form."""
        if not request.user.is_teacher:
            return HttpResponseForbidden('Only teachers can create courses.')
        form = CourseForm()
        return render(request, 'courses/course_create.html', {'form': form})

    def post(self, request):
        """Process the course creation form."""
        if not request.user.is_teacher:
            return HttpResponseForbidden('Only teachers can create courses.')
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, f'Course "{course.title}" created successfully.')
            return redirect('course-detail', pk=course.pk)
        return render(request, 'courses/course_create.html', {'form': form})


class CourseEditView(LoginRequiredMixin, View):
    """
    Edit an existing course.

    Only the course teacher can edit their own courses.
    """

    def get(self, request, pk):
        """Display the course edit form."""
        course = get_object_or_404(Course, pk=pk, teacher=request.user)
        form = CourseForm(instance=course)
        return render(request, 'courses/course_edit.html', {
            'form': form, 'course': course,
        })

    def post(self, request, pk):
        """Process the course edit form."""
        course = get_object_or_404(Course, pk=pk, teacher=request.user)
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully.')
            return redirect('course-detail', pk=course.pk)
        return render(request, 'courses/course_edit.html', {
            'form': form, 'course': course,
        })


@login_required
def enroll(request, pk):
    """
    Enrol the current student in a course.

    Requirement R1(e): Students should be able to enrol themselves on a course.
    Creates an Enrollment record and triggers a notification to the teacher
    via the post_save signal.
    """
    if request.method != 'POST':
        return redirect('course-detail', pk=pk)

    course = get_object_or_404(Course, pk=pk)

    if not request.user.is_student:
        messages.error(request, 'Only students can enrol in courses.')
        return redirect('course-detail', pk=pk)

    if course.is_full:
        messages.error(request, 'This course is full.')
        return redirect('course-detail', pk=pk)

    # Check for existing enrollment (may be blocked or dropped)
    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course,
        defaults={'status': Enrollment.Status.ACTIVE},
    )

    if not created:
        if enrollment.status == Enrollment.Status.BLOCKED:
            messages.error(request, 'You have been blocked from this course.')
        elif enrollment.status == Enrollment.Status.ACTIVE:
            messages.info(request, 'You are already enrolled in this course.')
        else:
            # Re-enrol a previously dropped student
            enrollment.status = Enrollment.Status.ACTIVE
            enrollment.dropped_at = None
            enrollment.save()
            messages.success(request, f'Re-enrolled in {course.title}.')
    else:
        messages.success(request, f'Successfully enrolled in {course.title}.')

    return redirect('course-detail', pk=pk)


@login_required
def unenroll(request, pk):
    """
    Remove the current student from a course.

    Sets the enrollment status to 'dropped' and records the timestamp.
    """
    if request.method != 'POST':
        return redirect('course-detail', pk=pk)

    enrollment = get_object_or_404(
        Enrollment,
        student=request.user,
        course_id=pk,
        status=Enrollment.Status.ACTIVE,
    )
    enrollment.status = Enrollment.Status.DROPPED
    enrollment.dropped_at = timezone.now()
    enrollment.save()
    messages.success(request, 'You have unenrolled from the course.')
    return redirect('course-list')


class CourseStudentListView(LoginRequiredMixin, View):
    """
    Display a list of students enrolled in a course.

    Requirement R1(h): Teachers should view their courses and see
    a list of students enrolled on their course.
    """

    def get(self, request, pk):
        """List enrolled students for a course (teacher only)."""
        course = get_object_or_404(Course, pk=pk, teacher=request.user)
        enrollments = course.enrollments.select_related('student').all()
        context = {
            'course': course,
            'enrollments': enrollments,
        }
        return render(request, 'courses/enrollment_list.html', context)


@login_required
def block_student(request, pk, student_id):
    """
    Block a student from a course.

    Requirement R1(h): Teachers should be able to block students.
    Sets the enrollment status to 'blocked'.
    """
    if request.method != 'POST':
        return redirect('course-students', pk=pk)

    course = get_object_or_404(Course, pk=pk, teacher=request.user)
    enrollment = get_object_or_404(
        Enrollment, course=course, student_id=student_id,
    )
    enrollment.status = Enrollment.Status.BLOCKED
    enrollment.save()
    messages.success(request, 'Student has been blocked from this course.')
    return redirect('course-students', pk=pk)


@login_required
def remove_student(request, pk, student_id):
    """
    Remove a student from a course.

    Sets the enrollment status to 'dropped' with a timestamp.
    """
    if request.method != 'POST':
        return redirect('course-students', pk=pk)

    course = get_object_or_404(Course, pk=pk, teacher=request.user)
    enrollment = get_object_or_404(
        Enrollment, course=course, student_id=student_id,
    )
    enrollment.status = Enrollment.Status.DROPPED
    enrollment.dropped_at = timezone.now()
    enrollment.save()
    messages.success(request, 'Student has been removed from this course.')
    return redirect('course-students', pk=pk)


class MaterialUploadView(LoginRequiredMixin, View):
    """
    Upload course materials.

    Requirement R1(j): Teachers should add files such as teaching materials
    to their account, accessible via the course home page.
    """

    def get(self, request, pk):
        """Display the material upload form."""
        course = get_object_or_404(Course, pk=pk, teacher=request.user)
        form = CourseMaterialForm()
        return render(request, 'courses/material_upload.html', {
            'form': form, 'course': course,
        })

    def post(self, request, pk):
        """Process the material upload form."""
        course = get_object_or_404(Course, pk=pk, teacher=request.user)
        form = CourseMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.course = course
            material.uploaded_by = request.user
            material.save()
            messages.success(request, f'Material "{material.title}" uploaded.')
            return redirect('course-detail', pk=pk)
        return render(request, 'courses/material_upload.html', {
            'form': form, 'course': course,
        })


class FeedbackCreateView(LoginRequiredMixin, View):
    """
    Submit feedback for a course.

    Requirement R1(f): Students should be able to leave feedback for
    a particular course. Only enrolled students can leave feedback,
    and each student can only submit one review per course.
    """

    def get(self, request, pk):
        """Display the feedback form."""
        course = get_object_or_404(Course, pk=pk)

        # Check that the student is enrolled
        if not Enrollment.objects.filter(
            student=request.user, course=course, status=Enrollment.Status.ACTIVE,
        ).exists():
            messages.error(request, 'You must be enrolled to leave feedback.')
            return redirect('course-detail', pk=pk)

        # Check for existing feedback
        if Feedback.objects.filter(student=request.user, course=course).exists():
            messages.info(request, 'You have already submitted feedback for this course.')
            return redirect('course-detail', pk=pk)

        form = FeedbackForm()
        return render(request, 'courses/feedback_form.html', {
            'form': form, 'course': course,
        })

    def post(self, request, pk):
        """Process the feedback form."""
        course = get_object_or_404(Course, pk=pk)
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.course = course
            feedback.student = request.user
            feedback.save()
            messages.success(request, 'Feedback submitted. Thank you!')
            return redirect('course-detail', pk=pk)
        return render(request, 'courses/feedback_form.html', {
            'form': form, 'course': course,
        })
