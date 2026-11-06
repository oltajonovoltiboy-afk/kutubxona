from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'student', 'O‘quvchi'
        TEACHER = 'teacher', 'O‘qituvchi'
        LIBRARIAN = 'librarian', 'Kutubxonachi'
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.STUDENT)
    group_name = models.CharField(max_length=50, blank=True, verbose_name='Guruh/sinf')
    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Kategoriya')
    description = models.CharField(max_length=250, blank=True, verbose_name='Tavsif')
    class Meta: ordering = ['name']; verbose_name_plural = 'Kategoriyalar'
    def __str__(self): return self.name

class Book(models.Model):
    title = models.CharField(max_length=240, verbose_name='Kitob nomi')
    author = models.CharField(max_length=180, verbose_name='Muallif')
    subject = models.CharField(max_length=100, blank=True, verbose_name='Fan')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='books')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    language = models.CharField(max_length=40, default='O‘zbek', verbose_name='Til')
    published_year = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1000), MaxValueValidator(2100)], verbose_name='Nashr yili')
    isbn = models.CharField(max_length=30, blank=True, verbose_name='ISBN')
    cover = models.ImageField(upload_to='covers/', blank=True, null=True, verbose_name='Muqova')
    pdf_file = models.FileField(upload_to='books/%Y/%m/', blank=True, validators=[FileExtensionValidator(['pdf'])], verbose_name='PDF fayl')
    external_url = models.URLField(blank=True, verbose_name='Tashqi havola')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='submitted_books')
    approved = models.BooleanField(default=False, verbose_name='Tasdiqlangan')
    featured = models.BooleanField(default=False, verbose_name='Tavsiya etilgan')
    created_at = models.DateTimeField(auto_now_add=True)
    view_count = models.PositiveIntegerField(default=0)
    class Meta: ordering = ['-featured', '-created_at']
    def __str__(self): return f'{self.title} — {self.author}'

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: constraints = [models.UniqueConstraint(fields=['user', 'book'], name='unique_user_book_favorite')]

class ReadingProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reading_progress')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='progress_records')
    current_page = models.PositiveIntegerField(default=1)
    total_pages = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'book'], name='unique_user_book_progress')]
    @property
    def percent(self):
        return min(100, round(self.current_page * 100 / self.total_pages)) if self.total_pages else 0

class ReadingEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reading_events')
    event_type = models.CharField(max_length=20, choices=[('open','Ochish'),('download','Yuklab olish')], default='open')
    created_at = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=180)
    message = models.TextField(max_length=1200)
    url = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
    def __str__(self): return self.title

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=100, blank=True)
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title
    @property
    def question_count(self): return self.questions.count()

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=1000)
    order = models.PositiveIntegerField(default=0)
    class Meta: ordering = ['order', 'id']
    def __str__(self): return self.text[:80]

class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    class Meta: ordering = ['id']
    def __str__(self): return self.text[:80]

class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    @property
    def percent(self): return round(self.score * 100 / self.total) if self.total else 0

class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    message = models.TextField(max_length=3000)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.name} — {self.created_at:%Y-%m-%d}'
