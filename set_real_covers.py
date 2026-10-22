import os
from urllib.request import Request, urlopen

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.settings')

import django
from django.core.files.base import ContentFile

django.setup()

from catalog.models import Book

covers = {
    '9780451524935': 'https://covers.openlibrary.org/b/isbn/9780451524935-L.jpg',
    '9788535912091': 'https://covers.openlibrary.org/b/isbn/9788535912091-L.jpg',
    '9788582850042': 'https://covers.openlibrary.org/b/isbn/9788582850042-L.jpg',
    '9788535911957': 'https://covers.openlibrary.org/b/isbn/9788535911957-L.jpg',
    '9788532530787': 'https://covers.openlibrary.org/b/isbn/9788532530787-L.jpg',
}

for book in Book.objects.filter(isbn__in=list(covers.keys())):
    url = covers.get(book.isbn)
    if not url:
        continue
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urlopen(req, timeout=30) as response:
            data = response.read()
        if not data:
            raise ValueError('Download vazio')
        filename = f'{book.isbn}.jpg'
        book.image.save(filename, ContentFile(data), save=True)
        print(f'Atualizada capa de: {book.title}')
    except Exception as exc:
        print(f'Falha em {book.title}: {exc}')
