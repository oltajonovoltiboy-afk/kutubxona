import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import User, Book, Category, Quiz, Question, AnswerOption, ReadingProgress

class LibraryTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='student1', password='StrongPass123!', role='student')
        self.book = Book.objects.create(title='Python asoslari', author='Ali Valiyev', subject='Informatika', description='Dasturlash kitobi', approved=True)

    def test_home_shows_approved_books_and_searches(self):
        response = self.client.get(reverse('home'), {'q':'Python'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python asoslari')
        self.assertEqual(self.client.get(reverse('home'), {'q':'bo‘lmagan kitob'}).context['page_obj'].paginator.count, 0)

    def test_unapproved_book_is_not_public(self):
        pending = Book.objects.create(title='Tekshiruvda', author='Muallif', approved=False)
        self.assertEqual(self.client.get(reverse('book_detail', args=[pending.pk])).status_code, 404)

    def test_pdf_reader_requires_login(self):
        self.assertEqual(self.client.get(reverse('book_pdf', args=[self.book.pk])).status_code, 302)

    def test_student_cannot_upload_book(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse('upload_book')).status_code, 403)

    def test_progress_endpoint_saves_user_progress(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('save_progress', args=[self.book.pk]), data=json.dumps({'page':5,'total':20}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        progress = ReadingProgress.objects.get(user=self.student, book=self.book)
        self.assertEqual(progress.current_page, 5)
        self.assertEqual(progress.percent, 25)

    def test_ai_helper_returns_catalog_sources(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('ai_librarian'), data=json.dumps({'question':'Python asoslari'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['sources'][0]['title'], 'Python asoslari')

    def test_quiz_is_graded_server_side(self):
        self.client.force_login(self.student)
        quiz = Quiz.objects.create(title='Python testi', is_published=True)
        question = Question.objects.create(quiz=quiz, text='Python nima?')
        right = AnswerOption.objects.create(question=question, text='Dasturlash tili', is_correct=True)
        AnswerOption.objects.create(question=question, text='Brauzer')
        response = self.client.post(reverse('take_quiz', args=[quiz.pk]), {f'q_{question.pk}': str(right.pk)})
        self.assertEqual(response.status_code, 302)
        from .models import QuizAttempt
        self.assertEqual(QuizAttempt.objects.get(user=self.student, quiz=quiz).score, 1)
