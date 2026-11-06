from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse
import csv
from .models import (User, Book, Category, Favorite, ReadingEvent, ReadingProgress, Notification,
                     Quiz, Question, AnswerOption, QuizAttempt, ContactMessage)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Litsey ma’lumotlari', {'fields': ('role','group_name')}),)
    list_display = ('username','first_name','last_name','role','group_name','is_active','is_staff')
    list_filter = ('role','is_active','is_staff','group_name')
    search_fields = ('username','first_name','last_name','email','group_name')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title','author','subject','approved','featured','view_count','created_at')
    list_filter = ('approved','featured','subject','language','category')
    search_fields = ('title','author','subject','description','isbn')
    list_editable = ('approved','featured')
    readonly_fields = ('view_count','created_at')
    actions = ('export_as_csv',)

    @admin.action(description='Tanlangan kitoblarni CSV formatida eksport qilish')
    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename=kutubxona-kitoblari.csv'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['Kitob nomi','Muallif','Fan','Kategoriya','Til','Nashr yili','Tasdiqlangan','Ko‘rishlar'])
        for book in queryset.select_related('category'):
            writer.writerow([book.title, book.author, book.subject, book.category.name if book.category else '', book.language, book.published_year or '', 'Ha' if book.approved else 'Yo‘q', book.view_count])
        return response

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin): search_fields = ('name',)

class AnswerInline(admin.TabularInline):
    model = AnswerOption; extra = 4
class QuestionInline(admin.StackedInline):
    model = Question; extra = 1
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title','subject','is_published','created_by','created_at')
    list_filter = ('is_published','subject')
    search_fields = ('title','description','subject')
    inlines = [QuestionInline]
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin): list_display = ('text','quiz','order'); inlines = [AnswerInline]
@admin.register(ContactMessage)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name','email','is_read','created_at'); list_filter = ('is_read','created_at'); search_fields = ('name','email','message')
admin.site.register([Favorite, ReadingEvent, ReadingProgress, Notification, QuizAttempt, AnswerOption])
admin.site.site_header = 'Urganch akademik litseyi — Kutubxona boshqaruvi'
admin.site.site_title = 'Raqamli kutubxona'
admin.site.index_title = 'Tizim boshqaruvi'
