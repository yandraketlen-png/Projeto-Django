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

for book in Book.objects.all():
    url = cover_map.get(book.title)
    if not url:
        continue

    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as response:
            data = response.read()
        if data:
            filename = f"{book.isbn or book.title.replace(' ', '_')}.jpg"
            book.image.save(filename, ContentFile(data), save=True)
            print(f'Atualizada: {book.title}')
    except Exception as exc:
        print(f'Falha: {book.title} -> {exc}')
