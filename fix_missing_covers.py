import os
from urllib.request import Request, urlopen

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.settings')

import django
from django.core.files.base import ContentFile

django.setup()

from catalog.models import Book

cover_map = {
    '1984': 'https://covers.openlibrary.org/b/isbn/9780451524935-L.jpg',
    'A Revolução dos Bichos': 'https://covers.openlibrary.org/b/isbn/9788535911957-L.jpg',
    'Dom Casmurro': 'https://covers.openlibrary.org/b/isbn/9788535912091-L.jpg',
    'Harry Potter e a Pedra Filosofal': 'https://covers.openlibrary.org/b/isbn/9788532530787-L.jpg',
    'O Pequeno Príncipe': 'https://covers.openlibrary.org/b/isbn/9788582850042-L.jpg',
    'A Menina Mais Fria de Coldtown': 'https://m.media-amazon.com/images/I/81n8N1Z0mOL.jpg',
    'As Crônicas de Nárnia': 'https://m.media-amazon.com/images/I/91L2B1dInEL.jpg',
    'The house of nigth (Marcada)': 'https://m.media-amazon.com/images/I/71cxnlfenLL.jpg',
}

isbn_map = {
    'AMM12550': 'https://m.media-amazon.com/images/I/81n8N1Z0mOL.jpg',
    'crn1222': 'https://m.media-amazon.com/images/I/91L2B1dInEL.jpg',
    'THOF12005': 'https://m.media-amazon.com/images/I/71cxnlfenLL.jpg',
}

updated = 0
missing = []

for book in Book.objects.all():
    if book.image and book.image.name:
        continue

    url = cover_map.get(book.title)
    if not url:
        url = isbn_map.get(book.isbn)
    if not url:
        missing.append((book.title, book.isbn))
        continue

    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as response:
            data = response.read()
        if not data:
            raise ValueError('download vazio')
        filename = f"{book.isbn or book.title.replace(' ', '_')}.jpg"
        book.image.save(filename, ContentFile(data), save=True)
        updated += 1
        print(f'Atualizada: {book.title}')
    except Exception as exc:
        print(f'Falha: {book.title} -> {exc}')

print(f'Atualizadas: {updated}')
print(f'Faltando mapeamento: {missing}')
