import json
import re
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import FileResponse, Http404, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_GET
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import RegisterForm, BookForm, ContactForm
from .search import search_books, STOPWORDS
from .models import (Book, Favorite, ReadingEvent, ReadingProgress, Category, Quiz,
                     QuizAttempt, Notification)

def home(request):
    query = request.GET.get('q', '').strip()
    subject = request.GET.get('subject', '').strip()
    language = request.GET.get('language', '').strip()
    category_id = request.GET.get('category', '').strip()
    books = Book.objects.filter(approved=True).select_related('category')
    if subject: books = books.filter(subject__iexact=subject)
    if language: books = books.filter(language__iexact=language)
    if category_id.isdigit(): books = books.filter(category_id=int(category_id))
    if query: books = search_books(books, query)  # kirill/lotin, harf registri va imlo xatolariga chidamli
    paginator = Paginator(books, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    favorites = set(Favorite.objects.filter(user=request.user).values_list('book_id', flat=True)) if request.user.is_authenticated else set()
    subjects = Book.objects.filter(approved=True).exclude(subject='').values_list('subject', flat=True).distinct().order_by('subject')
    languages = Book.objects.filter(approved=True).values_list('language', flat=True).distinct().order_by('language')
    return render(request, 'catalog/home.html', {
        'books': page_obj.object_list, 'page_obj': page_obj, 'query': query, 'favorites': favorites,
        'categories': Category.objects.all(), 'subjects': subjects, 'languages': languages,
        'selected_subject': subject, 'selected_language': language, 'selected_category': category_id,
        'featured_books': Book.objects.filter(approved=True, featured=True)[:4],
        'book_count': Book.objects.filter(approved=True).count(),
        'quiz_count': Quiz.objects.filter(is_published=True).count(),
    })

def register(request):
    if request.user.is_authenticated: return redirect('home')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False); user.role = 'student'; user.save()
        login(request, user)
        messages.success(request, 'Hisobingiz yaratildi. Raqamli kutubxonaga xush kelibsiz!')
        return redirect('dashboard')
    return render(request, 'catalog/form_page.html', {'form': form, 'title': 'Ro‘yxatdan o‘tish', 'subtitle':'Kutubxona xizmatlaridan foydalanish uchun hisob yarating.'})

def login_view(request):
    if request.user.is_authenticated: return redirect('dashboard')
    error = None
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username','').strip(), password=request.POST.get('password',''))
        if user is not None and user.is_active:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or ''
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()): return redirect(next_url)
            return redirect('dashboard')
        error = 'Login yoki parol noto‘g‘ri.'
    return render(request, 'catalog/login.html', {'error': error, 'next': request.GET.get('next','')})

@require_POST
def logout_view(request):
    logout(request); messages.info(request, 'Tizimdan xavfsiz chiqdingiz.'); return redirect('home')

def book_detail(request, pk):
    book = get_object_or_404(Book.objects.select_related('category'), pk=pk, approved=True)
    Book.objects.filter(pk=pk).update(view_count=book.view_count + 1)
    ReadingEvent.objects.create(user=request.user if request.user.is_authenticated else None, book=book, event_type='open')
    progress = ReadingProgress.objects.filter(user=request.user, book=book).first() if request.user.is_authenticated else None
    is_favorite = request.user.is_authenticated and Favorite.objects.filter(user=request.user, book=book).exists()
    return render(request, 'catalog/book_detail.html', {'book': book, 'progress': progress, 'is_favorite': is_favorite})

@login_required
def book_pdf(request, pk):
    book = get_object_or_404(Book, pk=pk, approved=True)
    if book.pdf_file:
        ReadingEvent.objects.create(user=request.user, book=book, event_type='open')
        progress, _ = ReadingProgress.objects.get_or_create(user=request.user, book=book)
        return render(request, 'catalog/reader.html', {'book': book, 'progress': progress})
    if book.external_url: return redirect(book.external_url)
    raise Http404('Bu kitob uchun PDF hali yuklanmagan.')

@login_required
def book_pdf_file(request, pk):
    book = get_object_or_404(Book, pk=pk, approved=True)
    if not book.pdf_file:
        if book.external_url: return redirect(book.external_url)
        raise Http404('Bu kitob uchun PDF hali yuklanmagan.')
    # Stream the PDF through an authenticated endpoint; do not expose a public media URL in the reader.
    safe_name = ''.join(ch for ch in book.title if ch.isalnum() or ch in (' ', '-', '_')).strip()[:100] or 'kitob'
    return FileResponse(book.pdf_file.open('rb'), content_type='application/pdf', as_attachment=False, filename=f'{safe_name}.pdf')

@login_required
@require_POST
def save_progress(request, pk):
    book = get_object_or_404(Book, pk=pk, approved=True)
    try:
        data = json.loads(request.body or '{}')
        page = max(1, min(int(data.get('page', 1)), 1000000))
        total = max(0, min(int(data.get('total', 0)), 1000000))
    except (ValueError, TypeError, json.JSONDecodeError): return JsonResponse({'ok': False, 'error': 'Noto‘g‘ri ma’lumot'}, status=400)
    progress, _ = ReadingProgress.objects.get_or_create(user=request.user, book=book)
    progress.current_page = page; progress.total_pages = total; progress.save(update_fields=['current_page','total_pages','updated_at'])
    return JsonResponse({'ok': True, 'page': progress.current_page, 'percent': progress.percent})

@login_required
@require_POST
def toggle_favorite(request, pk):
    book = get_object_or_404(Book, pk=pk, approved=True)
    obj, created = Favorite.objects.get_or_create(user=request.user, book=book)
    if not created: obj.delete()
    messages.success(request, 'Sevimlilar ro‘yxati yangilandi.')
    next_url = request.POST.get('next') or 'home'
    return redirect(next_url if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()) else 'home')

@login_required
def favorites(request):
    books = Book.objects.filter(favorites__user=request.user, approved=True).select_related('category')
    return render(request, 'catalog/favorites.html', {'books': books})

@login_required
def dashboard(request):
    progress = ReadingProgress.objects.filter(user=request.user).select_related('book').order_by('-updated_at')[:6]
    favorites = Book.objects.filter(favorites__user=request.user, approved=True)[:6]
    attempts = QuizAttempt.objects.filter(user=request.user).select_related('quiz').order_by('-created_at')[:5]
    notifications = request.user.notifications.filter(is_read=False)[:5]
    return render(request, 'catalog/dashboard.html', {'progress':progress,'favorites':favorites,'attempts':attempts,'notifications':notifications})

@login_required
def upload_book(request):
    if request.user.role not in ('teacher', 'librarian') and not request.user.is_staff: raise PermissionDenied
    form = BookForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        book = form.save(commit=False); book.submitted_by = request.user
        book.approved = bool(request.user.is_staff or request.user.role == 'librarian'); book.save()
        messages.success(request, 'Kitob qabul qilindi. Tasdiqlash talab qilinsa, moderator tekshiruvidan keyin katalogda chiqadi.')
        return redirect('dashboard')
    return render(request, 'catalog/form_page.html', {'form': form, 'title': 'Kitob yuborish', 'subtitle':'Kitob ma’lumotlarini to‘ldiring. Nashr katalogga chiqishidan oldin tekshirilishi mumkin.'})

def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Murojaatingiz yuborildi. Rahmat!'); return redirect('contact')
    return render(request, 'catalog/form_page.html', {'form': form, 'title': 'Biz bilan bog‘lanish', 'subtitle':'Taklif va xabarlaringiz kutubxonani yaxshilashga yordam beradi.'})

@login_required
def create_quiz(request):
    if request.user.role not in ('teacher', 'librarian') and not request.user.is_staff:
        raise PermissionDenied
    errors = []
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()[:200]
        subject = request.POST.get('subject', '').strip()[:100]
        description = request.POST.get('description', '').strip()[:3000]
        prepared = []
        if not title:
            errors.append('Test nomini kiriting.')
        for i in range(1, 6):
            text = request.POST.get(f'question_{i}', '').strip()[:1000]
            if not text:
                continue
            options = [request.POST.get(f'option_{i}_{j}', '').strip()[:500] for j in range(1, 5)]
            nonempty = [(idx + 1, value) for idx, value in enumerate(options) if value]
            correct = request.POST.get(f'correct_{i}', '')
            if len(nonempty) < 2:
                errors.append(f'{i}-savol uchun kamida 2 ta javob variantini kiriting.')
            elif correct not in {str(idx) for idx, _ in nonempty}:
                errors.append(f'{i}-savol uchun to‘g‘ri javobni belgilang.')
            else:
                prepared.append((text, nonempty, int(correct)))
        if not prepared:
            errors.append('Kamida bitta savol kiriting.')
        if not errors:
            quiz = Quiz.objects.create(title=title, subject=subject, description=description,
                created_by=request.user, is_published=bool(request.user.is_staff or request.user.role == 'librarian'))
            from .models import Question, AnswerOption
            for order, (text, options, correct) in enumerate(prepared, start=1):
                question = Question.objects.create(quiz=quiz, text=text, order=order)
                for index, option_text in options:
                    AnswerOption.objects.create(question=question, text=option_text, is_correct=(index == correct))
            if quiz.is_published:
                messages.success(request, 'Test yaratildi va nashr qilindi.')
            else:
                messages.success(request, 'Test yuborildi. Administrator tekshirganidan keyin e’lon qilinadi.')
            return redirect('dashboard')
    return render(request, 'catalog/create_quiz.html', {'errors': errors, 'question_numbers': range(1, 6), 'option_numbers': range(1, 5)})

def quiz_list(request):
    quizzes = Quiz.objects.filter(is_published=True).annotate(num_questions=Count('questions')).order_by('title')
    return render(request, 'catalog/quiz_list.html', {'quizzes':quizzes})

@login_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('questions__options'), pk=pk, is_published=True)
    questions = list(quiz.questions.all())
    if request.method == 'POST':
        score = 0
        for question in questions:
            answer_id = request.POST.get(f'q_{question.pk}')
            if answer_id and question.options.filter(pk=answer_id, is_correct=True).exists(): score += 1
        attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz, score=score, total=len(questions))
        messages.success(request, f'Test yakunlandi: {score}/{len(questions)} ({attempt.percent}%).')
        return redirect('quiz_result', pk=attempt.pk)
    return render(request, 'catalog/take_quiz.html', {'quiz':quiz,'questions':questions})

@login_required
def quiz_result(request, pk):
    attempt = get_object_or_404(QuizAttempt.objects.select_related('quiz'), pk=pk, user=request.user)
    return render(request, 'catalog/quiz_result.html', {'attempt':attempt})

@login_required
@require_POST
def mark_notification_read(request, pk):
    note = get_object_or_404(Notification, pk=pk, user=request.user); note.is_read = True; note.save(update_fields=['is_read'])
    return redirect('dashboard')

@login_required
@require_POST
def ai_librarian(request):
    """Grounded catalogue helper; does not pretend to be a configured external AI model."""
    try: data = json.loads(request.body or '{}'); question = str(data.get('question','')).strip()[:500]
    except (json.JSONDecodeError, AttributeError): return JsonResponse({'answer':'Savolni qayta yuboring.','sources':[]}, status=400)
    if len(question) < 3: return JsonResponse({'answer':'Iltimos, savolingizni biroz batafsilroq yozing.','sources':[]})
    matches = search_books(Book.objects.filter(approved=True), question, limit=5, ignore_words=STOPWORDS)
    if matches:
        sources = [{'title':b.title,'author':b.author,'url':f'/kitob/{b.pk}/'} for b in matches]
        answer = 'Katalogdan savolingizga aloqador bo‘lishi mumkin bo‘lgan manbalarni topdim. Kitob tavsiflari to‘liq javob bermasligi mumkin — manbani ochib tekshiring.\n\n' + '\n'.join(f'• {b.title} — {b.author}' for b in matches)
    else:
        sources=[]; answer='Hozirgi katalogdagi ma’lumotlardan aniq mos manba topilmadi. Boshqa kalit so‘z bilan qidiring yoki kutubxonachiga murojaat qiling. Bu yordamchi hozircha katalog qidiruvi bilan ishlaydi; tashqi generativ AI xizmati ulanmagan.'
    return JsonResponse({'answer':answer,'sources':sources})


def service_worker(request):
    from pathlib import Path
    source = Path(__file__).resolve().parent / 'static' / 'catalog' / 'sw.js'
    response = HttpResponse(source.read_text(encoding='utf-8'), content_type='application/javascript; charset=utf-8')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response


@require_GET
def online_book_search(request):
    """Tashqi kataloglardan qidirish: Ziyouz, Open Library va Google Books."""
    import html as html_lib
    import urllib.parse
    import urllib.request
    from django.core.cache import cache

    query = request.GET.get('q', '').strip()[:140]
    if len(query) < 2:
        return JsonResponse({'results': [], 'providers': []})
    cache_key = 'online-books-v2:' + query.casefold()
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse(cached)

    headers = {'User-Agent': 'Mozilla/5.0 (compatible; UrganchLibrary/2.0)'}
    results, providers = [], []
    def add(item):
        title = (item.get('title') or '').strip()
        if title:
            item['title'] = title[:240]
            item['author'] = (item.get('author') or 'Muallif ko‘rsatilmagan')[:180]
            for field in ('url', 'pdf', 'read_url', 'cover'):
                value = item.get(field, '')
                if value and not value.startswith(('https://', 'http://')):
                    item[field] = ''
            results.append(item)

    # Ziyouz WordPress API.
    for domain in ('https://ziyouz.uz', 'https://ziyouz.com'):
        try:
            url = domain + '/wp-json/wp/v2/posts?' + urllib.parse.urlencode({'search': query, 'per_page': 20})
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=7) as response:
                posts = json.loads(response.read(3000000).decode('utf-8', 'ignore'))
            if isinstance(posts, list):
                for post in posts:
                    title_html = (post.get('title') or {}).get('rendered', '')
                    title = html_lib.unescape(re.sub(r'<[^>]+>', '', title_html)).strip()
                    body = (post.get('content') or {}).get('rendered', '')
                    pdfs = re.findall(r"https?://[^\s\"'<>]+?\.pdf(?:\?[^\s\"'<>]*)?", body, re.I)
                    add({'title': title, 'author': 'Ziyouz kutubxonasi', 'url': post.get('link', domain), 'pdf': pdfs[0] if pdfs else '', 'source': 'Ziyouz'})
                providers.append('Ziyouz')
        except Exception:
            pass

    # n.ziyouz.com Joomla katalogi — PDF havolalari to‘g‘ridan-to‘g‘ri olinadi.
    try:
        from html.parser import HTMLParser
        search_url = 'https://n.ziyouz.com/index.php?' + urllib.parse.urlencode({'option': 'com_search', 'searchword': query, 'searchphrase': 'all', 'ordering': 'newest'})
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
            page_html = response.read(2500000).decode('utf-8', 'ignore')
            page_url = response.geturl()
        for href in re.findall(r'''(?:href|src)\s*=\s*["']([^"']+)["']''', page_html, re.I):
            full_url = urllib.parse.urljoin(page_url, href.replace('&amp;', '&'))
            if 'n.ziyouz.com' in urllib.parse.urlsplit(full_url).hostname.lower() and ('.pdf' in full_url.lower() or '/books/' in full_url.lower()):
                label = urllib.parse.unquote(full_url.rsplit('/', 1)[-1]).replace('.pdf', '').replace('_', ' ')
                add({'title': label, 'author': 'n.ziyouz.com fondidan', 'url': full_url, 'pdf': full_url if '.pdf' in full_url.lower() else '', 'source': 'n.ziyouz.com'})
        providers.append('n.ziyouz.com')
    except Exception:
        pass

    # Open Library.
    try:
        url = 'https://openlibrary.org/search.json?' + urllib.parse.urlencode({'q': query, 'limit': 20, 'fields': 'key,title,author_name,cover_i,ia,ebook_access'})
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=7) as response:
            data = json.loads(response.read(3000000).decode('utf-8', 'ignore'))
        for item in data.get('docs', []):
            key = item.get('key', '')
            ia = item.get('ia') or []
            ia_id = ia[0] if ia else ''
            pdf = ''
            if ia_id and item.get('ebook_access') == 'public':
                try:
                    meta_url = 'https://archive.org/metadata/' + urllib.parse.quote(ia_id)
                    meta_req = urllib.request.Request(meta_url, headers=headers)
                    with urllib.request.urlopen(meta_req, timeout=5) as meta_resp:
                        files = json.loads(meta_resp.read(1500000).decode('utf-8', 'ignore')).get('files', [])
                    pdf_file = next((f.get('name') for f in files if str(f.get('name', '')).lower().endswith('.pdf')), '')
                    if pdf_file:
                        pdf = 'https://archive.org/download/' + urllib.parse.quote(ia_id) + '/' + urllib.parse.quote(pdf_file)
                except Exception:
                    pass
            add({'title': item.get('title', ''), 'author': ', '.join(item.get('author_name') or []), 'url': 'https://openlibrary.org' + key if key else 'https://openlibrary.org', 'pdf': pdf, 'cover': ('https://covers.openlibrary.org/b/id/' + str(item['cover_i']) + '-M.jpg') if item.get('cover_i') else '', 'source': 'Open Library'})
        providers.append('Open Library')
    except Exception:
        pass

    # Google Books.
    try:
        url = 'https://www.googleapis.com/books/v1/volumes?' + urllib.parse.urlencode({'q': query, 'maxResults': 20, 'printType': 'books'})
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=7) as response:
            data = json.loads(response.read(3000000).decode('utf-8', 'ignore'))
        for item in data.get('items', []):
            info = item.get('volumeInfo') or {}
            access = item.get('accessInfo') or {}
            read_url = ''
            if access.get('viewability') in ('ALL_PAGES', 'PARTIAL'):
                read_url = 'https://books.google.com/books?id=' + urllib.parse.quote(item.get('id', '')) + '&printsec=frontcover&output=embed'
            images = info.get('imageLinks') or {}
            add({'title': info.get('title', ''), 'author': ', '.join(info.get('authors') or []), 'url': info.get('previewLink') or info.get('infoLink') or 'https://books.google.com', 'read_url': read_url, 'cover': (images.get('thumbnail') or '').replace('http://', 'https://'), 'source': 'Google Books'})
        providers.append('Google Books')
    except Exception:
        pass

    unique = {}
    for item in results:
        key = re.sub(r'[^a-z0-9]', '', (item['title'] + item['author']).casefold())
        old = unique.get(key)
        if not old or (not (old.get('pdf') or old.get('read_url')) and (item.get('pdf') or item.get('read_url'))):
            unique[key] = item
    query_terms = [term.casefold() for term in re.findall(r'[a-zA-Z0-9а-яА-ЯёЁўЎқҚғҒҳҲ]+', query) if len(term) > 1]
    def relevance(item):
        title = item['title'].casefold()
        author = item['author'].casefold()
        score = sum(4 if term in title else 1 if term in author else 0 for term in query_terms)
        if query.casefold() in title:
            score += 8
        if item.get('pdf') or item.get('read_url'):
            score += 2
        return score
    ranked = sorted(unique.values(), key=relevance, reverse=True)
    payload = {'results': ranked[:60], 'providers': list(dict.fromkeys(providers))}
    cache.set(cache_key, payload, 600)
    return JsonResponse(payload)


@login_required
def online_book_reader(request):
    """PDF yoki ruxsat etilgan elektron kitob sahifasini sayt ichida ko‘rsatadi."""
    url = request.GET.get('url', '').strip()
    embed = request.GET.get('embed', '').strip()
    title = request.GET.get('title', 'Onlayn kitob')[:240]
    if url:
        if not _host_ok(url):
            raise Http404('Bu PDF manbasini ichki o‘quvchida ochib bo‘lmaydi.')
        return render(request, 'catalog/online_reader.html', {'book_title': title, 'pdf_url': url})
    if embed:
        # Faqat katalogda ishlatiladigan tanish elektron kutubxona domenlari.
        from urllib.parse import urlsplit, urljoin
        host = (urlsplit(embed).hostname or '').lower()
        allowed = ('ziyouz.com', 'ziyouz.uz', 'n.ziyouz.com', 'books.google.com', 'openlibrary.org', 'archive.org')
        if urlsplit(embed).scheme not in ('http', 'https') or not any(host == h or host.endswith('.' + h) for h in allowed):
            raise Http404('Bu elektron manbani ichki oynada ochishga ruxsat yo‘q.')
        # Ziyouz kitob sahifasida PDF biriktirilgan bo‘lsa, uni iframe emas,
        # saytning PDF.js o‘quvchisida ochamiz.
        if any(host == h or host.endswith('.' + h) for h in ('ziyouz.com', 'ziyouz.uz', 'n.ziyouz.com')):
            try:
                with _opener.open(urllib.request.Request(embed, headers=_UA), timeout=10) as upstream:
                    if 'pdf' in (upstream.headers.get('Content-Type') or '').lower():
                        return render(request, 'catalog/online_reader.html', {'book_title': title, 'pdf_url': upstream.geturl()})
                    html_text = upstream.read(_PAGE_MAX_BYTES).decode('utf-8', errors='ignore')
                    base = upstream.geturl()
                candidates = _re.findall(r'(?:href|src|data-src|data-url)\s*=\s*["\']([^"\']+?\.pdf(?:\?[^"\']*)?)["\']', html_text, _re.I)
                for candidate in candidates:
                    pdf_candidate = urljoin(base, candidate.replace('&amp;', '&'))
                    if _host_ok(pdf_candidate):
                        return render(request, 'catalog/online_reader.html', {'book_title': title, 'pdf_url': pdf_candidate})
            except Exception:
                pass
        return render(request, 'catalog/online_reader.html', {'book_title': title, 'embed_url': embed})
    raise Http404('Kitob manzili berilmagan.')


def ziyouz_search_api(request):
    """Ziyouz.com / Ziyouz.uz / n.ziyouz.com API qidiruv endpointi."""
    import re
    import urllib.parse
    import urllib.request
    from html import unescape

    q = request.GET.get('q', '').strip()[:150]
    if len(q) < 2:
        return JsonResponse({'results': []})

    results = []
    headers = {'User-Agent': 'Mozilla/5.0 (UrganchLibrary/1.0)'}

    # 1. WordPress REST API (ziyouz.uz & ziyouz.com)
    for domain in ('https://ziyouz.uz', 'https://ziyouz.com'):
        api_url = f"{domain}/wp-json/wp/v2/posts?search={urllib.parse.quote(q)}&per_page=10"
        req = urllib.request.Request(api_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                items = json.loads(resp.read().decode('utf-8', errors='ignore'))
                if isinstance(items, list):
                    for post in items:
                        raw_title = unescape(re.sub(r'<[^>]+>', '', (post.get('title') or {}).get('rendered', '')).strip())
                        if not raw_title:
                            continue
                        content_html = (post.get('content') or {}).get('rendered', '')
                        pdf_match = re.search(r'''https?://[^\s"'<>]+\.pdf''', content_html, re.I)
                        pdf_url = pdf_match.group(0) if pdf_match else ''
                        results.append({
                            'title': raw_title,
                            'author': 'Ziyouz.com kutubxonasi',
                            'url': post.get('link') or domain,
                            'pdf': pdf_url,
                            'source': 'Ziyouz.com API',
                        })
        except Exception:
            pass

    # 2. n.ziyouz.com qidiruvi
    search_url = f"https://n.ziyouz.com/index.php?option=com_search&searchword={urllib.parse.quote(q)}&searchphrase=all&ordering=newest"
    req = urllib.request.Request(search_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            html_text = resp.read().decode('utf-8', errors='ignore')
            for href, label in re.findall(r'<a[^>]+href=["\']([^"\']+\.pdf)["\'][^>]*>(.*?)</a>', html_text, re.I | re.S):
                if href.startswith('/'):
                    href = 'https://n.ziyouz.com' + href
                clean_label = unescape(re.sub(r'<[^>]+>', '', label)).strip() or urllib.parse.unquote(href.rsplit('/', 1)[-1])
                results.append({
                    'title': clean_label,
                    'author': 'n.ziyouz.com fondidan',
                    'url': href,
                    'pdf': href,
                    'source': 'n.ziyouz.com',
                })
    except Exception:
        pass

    return JsonResponse({'results': results[:24]})


# ---------------------------------------------------------------------------
# PDF proksi va PDF topuvchi (qidiruv natijasidagi kitobni sayt ichida PDF
# ko'rinishida o'qish uchun). Brauzer CORS cheklovlarini chetlab o'tadi.
# ---------------------------------------------------------------------------
import ipaddress
import re as _re
import socket
import urllib.error
import urllib.parse
import urllib.request
from django.conf import settings as _settings
from django.http import StreamingHttpResponse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET

_PDF_HOSTS = ('ziyouz.com', 'ziyouz.uz', 'archive.org', 'openlibrary.org')
_PDF_MAX_BYTES = 300 * 1024 * 1024
_PAGE_MAX_BYTES = 2 * 1024 * 1024
_UA = {'User-Agent': 'Mozilla/5.0 (UrganchLibrary/1.0)'}


def _allowed_hosts():
    extra = getattr(_settings, 'PDF_PROXY_EXTRA_HOSTS', ())
    return tuple(_PDF_HOSTS) + tuple(extra)


def _host_ok(url):
    """Faqat ishonchli domenlarga (va ularning subdomenlariga) ruxsat; ichki IP lar taqiqlangan."""
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    if parts.scheme not in ('http', 'https') or not parts.hostname:
        return False
    host = parts.hostname.lower()
    if not any(host == h or host.endswith('.' + h) for h in _allowed_hosts()):
        return False
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
    except Exception:
        return False
    return True


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _host_ok(newurl):
            raise urllib.error.URLError('Ruxsat etilmagan yo\'naltirish')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_SafeRedirect)


@require_GET
@xframe_options_sameorigin
def pdf_proxy(request):
    """/api/pdf/?url=...  — tashqi PDF ni (Range qo'llab-quvvatlanadi) o'zimiz orqali beradi."""
    url = request.GET.get('url', '').strip()
    if not _host_ok(url):
        return JsonResponse({'error': 'Bu manbadan o\'qishga ruxsat yo\'q.'}, status=400)
    headers = dict(_UA)
    if request.headers.get('Range'):
        headers['Range'] = request.headers['Range']
    try:
        upstream = _opener.open(urllib.request.Request(url, headers=headers), timeout=20)
    except urllib.error.HTTPError as e:
        return JsonResponse({'error': f'Manba {e.code} javob berdi.'}, status=502)
    except Exception:
        return JsonResponse({'error': 'Manbaga ulanib bo\'lmadi.'}, status=502)

    ctype = (upstream.headers.get('Content-Type') or '').lower()
    first = upstream.read(1024)
    if 'pdf' not in ctype and not first.lstrip().startswith(b'%PDF'):
        upstream.close()
        return JsonResponse({'error': 'Bu havola PDF fayl emas.'}, status=415)
    length = upstream.headers.get('Content-Length')
    if length and length.isdigit() and int(length) > _PDF_MAX_BYTES:
        upstream.close()
        return JsonResponse({'error': 'Fayl juda katta.'}, status=413)

    def stream():
        sent = len(first)
        yield first
        try:
            while sent < _PDF_MAX_BYTES:
                chunk = upstream.read(64 * 1024)
                if not chunk:
                    break
                sent += len(chunk)
                yield chunk
        finally:
            upstream.close()

    resp = StreamingHttpResponse(stream(), status=upstream.status if upstream.status in (200, 206) else 200,
                                 content_type='application/pdf')
    for h in ('Content-Length', 'Content-Range', 'Accept-Ranges'):
        if upstream.headers.get(h):
            resp[h] = upstream.headers[h]
    resp['Content-Disposition'] = 'inline'
    resp['Cache-Control'] = 'public, max-age=3600'
    return resp


@require_GET
def pdf_resolve(request):
    """/api/pdf-topish/?url=<kitob sahifasi>  — sahifadan PDF havolasini topadi."""
    page = request.GET.get('url', '').strip()
    if not _host_ok(page):
        return JsonResponse({'pdf': ''})
    try:
        with _opener.open(urllib.request.Request(page, headers=_UA), timeout=12) as resp:
            if 'pdf' in (resp.headers.get('Content-Type') or '').lower():
                return JsonResponse({'pdf': resp.geturl()})
            html_text = resp.read(_PAGE_MAX_BYTES).decode('utf-8', errors='ignore')
            base = resp.geturl()
    except Exception:
        return JsonResponse({'pdf': ''})
    found = []
    for href in _re.findall(r'(?:href|src|data-src|data-url)\s*=\s*["\']([^"\']+?\.pdf(?:\?[^"\']*)?)["\']', html_text, _re.I):
        full = urllib.parse.urljoin(base, href.replace('&amp;', '&'))
        if full not in found and _host_ok(full):
            found.append(full)
    if not found:
        for full in _re.findall(r'https?://[^\s"\'<>]+?\.pdf', html_text, _re.I):
            if full not in found and _host_ok(full):
                found.append(full)
    return JsonResponse({'pdf': found[0] if found else '', 'all': found[:5]})
