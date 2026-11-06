from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from catalog import views
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('service-worker.js', views.service_worker, name='service_worker'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('parolni-tiklash/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html', email_template_name='registration/password_reset_email.html', subject_template_name='registration/password_reset_subject.txt'), name='password_reset'),
    path('parol-tiklandi/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('parolni-tiklash/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('parol-yangilandi/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('kitob/<int:pk>/', views.book_detail, name='book_detail'),
    path('kitob/<int:pk>/pdf/', views.book_pdf, name='book_pdf'),
    path('kitob/<int:pk>/fayl/', views.book_pdf_file, name='book_pdf_file'),
    path('kitob/<int:pk>/progress/', views.save_progress, name='save_progress'),
    path('kitob/<int:pk>/sevimli/', views.toggle_favorite, name='toggle_favorite'),
    path('sevimlilar/', views.favorites, name='favorites'),
    path('kabinet/', views.dashboard, name='dashboard'),
    path('kitob-yuklash/', views.upload_book, name='upload_book'),
    path('testlar/', views.quiz_list, name='quiz_list'),
    path('test-yaratish/', views.create_quiz, name='create_quiz'),
    path('testlar/<int:pk>/', views.take_quiz, name='take_quiz'),
    path('test-natija/<int:pk>/', views.quiz_result, name='quiz_result'),
    path('bildirishnoma/<int:pk>/oqildi/', views.mark_notification_read, name='mark_notification_read'),
    path('api/kutubxonachi/', views.ai_librarian, name='ai_librarian'),
    path('api/ziyouz/', views.ziyouz_search_api, name='ziyouz_search_api'),
    path('api/online-search/', views.online_book_search, name='online_book_search'),
    path('onlayn-oqish/', views.online_book_reader, name='online_book_reader'),
    path('api/pdf/', views.pdf_proxy, name='pdf_proxy'),
    path('api/pdf-topish/', views.pdf_resolve, name='pdf_resolve'),
    path('murojaat/', views.contact, name='contact'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
