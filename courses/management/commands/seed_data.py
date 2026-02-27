"""
Management command to populate the database with demonstration data.

Creates sample teachers, students, courses, enrollments, materials,
feedback, status updates, and notifications for testing and demo purposes.

Usage:
    python manage.py seed_data
    python manage.py seed_data --clear   #  Delete existing data first
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from chat.models import ChatRoom, Message
from courses.models import Course, CourseMaterial, Enrollment, Feedback
from notifications.models import Notification

User = get_user_model()


class Command( BaseCommand):
    help = 'Populate the database with sample data for development and testing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing data before seeding.',
        )

    def handle(self, *args, **options ):
        if options['clear']:
            self.stdout.write(' Clearing existing data.. .')
            Message.objects.all().delete()
            ChatRoom.objects.all().delete()
            Notification.objects.all().delete()
            Feedback.objects.all().delete()
            CourseMaterial.objects.all().delete()
            Enrollment.objects.all().delete( )
            Course.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('All  data cleared.'))

        self.stdout.write('Creating seed data...')

         
        # Create superuser (admin)
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@elearning.local',
                'role': 'teacher',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(f'  Created admin user: admin / admin123')

         
        # Create teachers
         
        teachers_data = [
            {
                'username': 'prof_smith',
                'email': 'smith@elearning.local',
                'first_name': 'John',
                'last_name': 'Smith',
                'department': 'Computer Science',
            },
            {
                'username': 'prof_jones',
                'email': 'jones@elearning.local',
                'first_name': 'Sarah',
                'last_name': 'Jones',
                'department': 'Mathematics',
            },
            {
                'username': 'prof_williams',
                'email': 'williams@elearning.local',
                'first_name': 'Michael',
                'last_name': 'Williams',
                'department': 'Data Science',
            },
        ]

        teachers = []
        for data in teachers_data:
            dept = data.pop('department')
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={**data, 'role': 'teacher'},
            )
            if created:
                user.set_password('teacher123')
                user.save()
                # Update the auto-created profile
                user.profile.department = dept
                user.profile.bio = f'Professor of {dept} with years of teaching experience.'
                user.profile.save()
                self.stdout.write(f'  Created teacher: {user.username} / teacher123')
            teachers.append(user)

         
        # Create students
         
        students_data = [
            {
                'username': 'alice',
                'email': 'alice@elearning.local',
                'first_name': 'Alice',
                'last_name': 'Anderson',
                'student_id': 'STU001',
            },
            {
                'username': 'bob',
                'email': 'bob@elearning.local',
                'first_name': 'Bob',
                'last_name': 'Brown',
                'student_id': 'STU002',
            },
            {
                'username': 'charlie',
                'email': 'charlie@elearning.local',
                'first_name': 'Charlie',
                'last_name': 'Clark',
                'student_id': 'STU003',
            },
            {
                'username': 'diana',
                'email': 'diana@elearning.local',
                'first_name': 'Diana',
                'last_name': 'Davis',
                'student_id': 'STU004',
            },
            {
                'username': 'edward',
                'email': 'edward@elearning.local',
                'first_name': 'Edward',
                'last_name': 'Evans',
                'student_id': 'STU005',
            },
        ]

        students = []
        for data in students_data:
            sid = data.pop('student_id')
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={**data, 'role': 'student'},
            )
            if created:
                user.set_password('student123')
                user.save()
                user.profile.student_id = sid
                user.profile.enrollment_year = 2024
                user.profile.bio = f'Student passionate about learning new things.'
                user.profile.save()
                self.stdout.write(f'  Created student: {user.username} / student123')
            students.append(user)

         
        # Create courses
         
        courses_data = [
            {
                'teacher': teachers[0],
                'title': 'Introduction to Python Programming',
                'code': 'CS101',
                'description': (
                    'A comprehensive introduction to Python programming covering '
                    'variables, data types, control flow, functions, and object-oriented '
                    'programming. Ideal for beginners with no prior coding experience.'
                ),
                'category': 'Computer Science',
                'max_students': 30,
            },
            {
                'teacher': teachers[0],
                'title': 'Advanced Web Development',
                'code': 'CS301',
                'description': (
                    'Build modern web applications using Django, REST APIs, WebSockets, '
                    'and cloud deployment. Covers full-stack development including '
                    'frontend, backend, databases, and DevOps practices.'
                ),
                'category': 'Computer Science',
                'max_students': 25,
            },
            {
                'teacher': teachers[1],
                'title': 'Linear Algebra for Data Science',
                'code': 'MATH201',
                'description': (
                    'Foundational linear algebra concepts including vectors, matrices, '
                    'eigenvalues, and their applications in machine learning and data '
                    'analysis.'
                ),
                'category': 'Mathematics',
                'max_students': 40,
            },
            {
                'teacher': teachers[1],
                'title': 'Calculus II',
                'code': 'MATH102',
                'description': (
                    'Continuation of Calculus I covering integration techniques, '
                    'sequences, series, and multivariable calculus fundamentals.'
                ),
                'category': 'Mathematics',
                'max_students': 35,
            },
            {
                'teacher': teachers[2],
                'title': 'Machine Learning Fundamentals',
                'code': 'DS201',
                'description': (
                    'Introduction to machine learning algorithms including regression, '
                    'classification, clustering, and neural networks. Hands-on projects '
                    'using scikit-learn and TensorFlow.'
                ),
                'category': 'Data Science',
                'max_students': 20,
            },
        ]

        courses = []
        for data in courses_data:
            course, created = Course.objects.get_or_create(
                code=data['code'],
                defaults=data,
            )
            if created:
                self.stdout.write(f'  Created course: {course.code} - {course.title}')
            courses.append(course)

         
        # Create enrollments
         
        enrollment_pairs = [
            # CS101: alice, bob, charlie, diana
            (students[0], courses[0]),
            (students[1], courses[0]),
            (students[2], courses[0]),
            (students[3], courses[0]),
            # CS301: alice, bob
            (students[0], courses[1]),
            (students[1], courses[1]),
            # MATH201: alice, charlie, edward
            (students[0], courses[2]),
            (students[2], courses[2]),
            (students[4], courses[2]),
            # MATH102: diana, edward
            (students[3], courses[3]),
            (students[4], courses[3]),
            # DS201: bob, charlie, diana, edward
            (students[1], courses[4]),
            (students[2], courses[4]),
            (students[3], courses[4]),
            (students[4], courses[4]),
        ]

        for student, course in enrollment_pairs:
            enrollment, created = Enrollment.objects.get_or_create(
                student=student,
                course=course,
                defaults={'status': Enrollment.Status.ACTIVE},
            )
            if created:
                self.stdout.write(
                    f'  Enrolled {student.username} in {course.code}'
                )

         
        # Create feedback
         
        feedback_data = [
            (students[0] , courses[0], 5, 'Excellent course! Very well structured and easy to follow .'),
            (students[1], courses[0], 4, 'Good content but could use more practice exercises.'),
            (students[2], courses[0], 5, 'Professor Smith explains concepts really well.'),
            (students[0], courses[1], 4, 'Challenging but rewarding. The Django section was great.'),
            (students[0 ], courses[2], 5, 'Made linear algebra much more approachable.'),
            (students[2], courses[2], 4, 'Solid course with good real-world examples.'),
            (students[1], courses[4], 5, 'The hands-on ML projects were amazing.'),
            (students[4], courses[4], 4, 'Great introduction to machine learning concepts.') ,
        ]

        for student, course, rating, comment in feedback_data:
            fb, created = Feedback.objects.get_or_create(
                student=student,
                course=course,
                defaults={'rating': rating, 'comment': comment},
            )
            if created:
                self.stdout.write(
                    f'  Feedback by {student.username} for {course.code}: {rating}/5'
                )

    
        # Create status updates
        from accounts.models import StatusUpdate

        status_data = [
            (teachers[0], 'Just uploaded new Python exercises for CS101. Check them out!'),
            (teachers[1], 'Office hours this Thursday 2-4 PM in Room 301.'),
            (teachers[2], 'Exciting new ML dataset available for the final project.'),
            (students[0], 'Finally finished the Django REST API assignment!'),
            (students[1], 'Looking for a study group for the calculus midterm.'),
            (students[2], 'The CS101 Python course is fantastic so far.'),
        ]

        for user, content in status_data:
            StatusUpdate.objects.get_or_create(
                user=user,
                content=content,
            )

         
        # Create chat rooms and sample messages
         
        # Course group chat for CS101
        cs101_room, _ = ChatRoom.objects.get_or_create(
            course=courses[0],
            defaults={
                'name': f'{courses[0].code} Group Chat',
                'room_type': ChatRoom.RoomType.COURSE,
            },
        )
        cs101_room.participants.add(teachers[0], students[0], students[1], students[2], students[3])

        # DM between alice and prof_smith
        dm_room, dm_created = ChatRoom.objects.get_or_create(
            name='alice-prof_smith',
            room_type=ChatRoom.RoomType.DIRECT,
        )
        if dm_created:
            dm_room.participants.add(students[0], teachers[0])

        # Sample messages
        if not Message.objects.filter(room=cs101_room).exists():
            Message.objects.create(
                room=cs101_room,
                sender=teachers[0],
                content='Welcome to the CS101 group chat! Feel free to ask questions here.',
            )
            Message.objects.create(
                room=cs101_room,
                sender=students[0],
                content='Thanks Professor! Quick question about the first assignment.',
            )
            Message.objects.create(
                room=cs101_room,
                sender=teachers[0],
                content='Of course, go ahead Alice.',
            )
            self.stdout.write('  Created sample chat messages.')

        if not Message.objects.filter(room=dm_room).exists():
            Message.objects.create(
                room=dm_room,
                sender=students[0],
                content='Hi Professor, could I get an extension on the assignment?',
            )
            Message.objects.create(
                room=dm_room,
                sender=teachers[0],
                content='Hi Alice, sure. I can give you until Friday. Does that work?',
            )

         
        # Create sample notifications
        notif_data =  [
            {
                'recipient': teachers[0],
                'notification_type': 'enrollment',
                'title': 'New Enrollment in CS101',
                'message': 'Alice Anderson has enrolled in Introduction to Python Programming.',
                'link': f'/courses/{courses[0].pk}/',
            },
            {
                'recipient': students[0],
                'notification_type': 'new_material',
                'title': 'New Material in CS101',
                'message': 'Professor Smith uploaded "Week 1 Lecture Notes" to CS101.',
                'link': f'/courses/{courses[0].pk}/',
            },
            {
                'recipient': teachers[0],
                'notification_type': 'feedback',
                'title': 'New Feedback on CS101',
                'message': 'Alice Anderson left a 5-star review on your course.',
                'link': f'/courses/{courses[0].pk}/',
            },
        ]

        for data in notif_data:
            Notification.objects.get_or_create(
                recipient=data['recipient'],
                title=data['title'],
                defaults=data,
            )

        self.stdout.write(self.style.SUCCESS(
            '\nSeed data created successfully!\n\n'
            'Login credentials:\n'
            '  Admin:    admin / admin123\n'
            '  Teachers: prof_smith / teacher123\n'
            '            prof_jones / teacher123\n'
            '            prof_williams / teacher123\n'
            '  Students: alice / student123\n'
            '            bob / student123\n'
            '            charlie / student123\n'
            '            diana / student123\n'
            '            edward / student123\n'
        ))
