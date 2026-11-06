"""Xatolarga chidamli qidiruv.

- Katta/kichik harf farqi yo'q (kirill harflarida ham, SQLite'da ham ishlaydi).
- Kirill va lotin yozuvi bir xil qidiriladi: "ЎЗБЕК" == "o'zbek" == "OZBEK".
- Apostrof farqlari e'tiborga olinmaydi: o', o‘, oʻ, ў -> o.
- Imlo xatolari kechiriladi: "matematka" -> "Matematika", "adabyot" -> "Adabiyot".
"""
import math
import re
from difflib import SequenceMatcher

_CYR = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j',
    'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 's',
    'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': '', 'ь': '', 'ы': 'i', 'э': 'e', 'ю': 'yu',
    'я': 'ya', 'ў': 'o', 'қ': 'q', 'ғ': 'g', 'ҳ': 'h', 'ң': 'ng', 'ҷ': 'j',
}
_APOS = "'‘’ʻʼ`´′ʹ"
_TRANS = str.maketrans({**_CYR, **{c: '' for c in _APOS}})
_WORD = re.compile(r"[a-z0-9]+")

# Savol berilganda (AI kutubxonachi) ahamiyatsiz so'zlar
STOPWORDS = {
    'menga', 'kerak', 'bormi', 'bor', 'haqida', 'qanday', 'qaysi', 'kitob', 'kitoblar',
    'kitobi', 'tavsiya', 'ber', 'bering', 'va', 'bilan', 'uchun', 'nima', 'necha',
    'ayt', 'ayting', 'top', 'toping', 'izlayapman', 'qidiryapman', 'xohlayman', 'iltimos',
    'boyicha', 'doir', 'oid', 'mavzusida', 'mavzu',
}


def normalize(text):
    """Matnni qidiruv uchun yagona ko'rinishga keltiradi (kichik harf, lotin, apostrofsiz)."""
    return (text or '').lower().translate(_TRANS)


def tokenize(text):
    return _WORD.findall(normalize(text))


def _token_score(q, w):
    """So'rov so'zi q ning kitob so'zi w ga o'xshashligi (0..1)."""
    if q == w:
        return 1.0
    lq = len(q)
    if lq >= 2 and w.startswith(q):
        return 0.9
    if lq >= 3 and q in w:
        return 0.75
    if lq < 3 or abs(len(w) - lq) > max(3, lq):
        return 0.0
    thr = 0.8 if lq <= 4 else 0.72
    best = 0.0
    # to'liq so'z bilan va so'z boshi (yarim yozilgan so'z) bilan solishtirish
    for cand in (w, w[:lq + 1]):
        sm = SequenceMatcher(None, q, cand)
        if sm.real_quick_ratio() < thr or sm.quick_ratio() < thr:
            continue
        best = max(best, sm.ratio())
    return best * 0.85 if best >= thr else 0.0


def search_books(queryset, query, limit=None, ignore_words=None):
    """queryset ichidan query ga mos kitoblarni o'xshashlik bo'yicha tartiblab qaytaradi."""
    q_tokens = tokenize(query)
    if ignore_words:
        filtered = [t for t in q_tokens if t not in ignore_words]
        q_tokens = filtered or q_tokens
    if not q_tokens:
        return list(queryset)
    q_phrase = ' '.join(q_tokens)
    need = max(1, math.ceil(len(q_tokens) * 0.6))

    scored = []
    for book in queryset.select_related('category'):
        fields = (
            (3.0, tokenize(book.title)),
            (2.0, tokenize(book.author)),
            (1.5, tokenize(book.subject) + tokenize(book.category.name if book.category else '')),
            (2.0, tokenize(book.isbn)),
            (1.0, tokenize((book.description or '')[:600])),
        )
        total, matched = 0.0, 0
        for qt in q_tokens:
            best = 0.0
            for weight, words in fields:
                for w in words:
                    s = _token_score(qt, w)
                    if s:
                        best = max(best, s * weight)
                        if s == 1.0 and weight == 3.0:
                            break
            if best:
                matched += 1
                total += best
        if matched >= need:
            if q_phrase in ' '.join(tokenize(book.title)):
                total += 2.0
            scored.append((total, book))
    scored.sort(key=lambda x: (-x[0], -x[1].featured, -x[1].pk))
    result = [b for _, b in scored]
    return result[:limit] if limit else result
