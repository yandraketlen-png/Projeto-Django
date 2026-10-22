import os
from io import BytesIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.settings')

import django
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw

django.setup()

from catalog.models import Book

books = [
    ("Dom Casmurro", "Machado de Assis", "9788535912091", "#8B5E3C"),
    ("O Pequeno Príncipe", "Antoine de Saint-Exupéry", "9788582850042", "#E67E22"),
    ("1984", "George Orwell", "9780451524935", "#2C3E50"),
    ("A Revolução dos Bichos", "George Orwell", "9788535911957", "#3A7D44"),
    ("Harry Potter e a Pedra Filosofal", "J.K. Rowling", "9788532530787", "#D4A017"),
]

for title, author, isbn, color in books:
    if Book.objects.filter(isbn=isbn).exists():
        print(f"Já existe: {title}")
        continue

    image = Image.new("RGB", (400, 600), color)
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 380, 580), outline=(255, 255, 255), width=6)
    draw.text((40, 40), title[:22], fill=(255, 255, 255))
    draw.text((40, 500), author, fill=(255, 255, 255))

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    content = ContentFile(buffer.getvalue(), name=f"{isbn}.png")

    Book.objects.create(
        title=title,
        author=author,
        isbn=isbn,
        copies_total=2,
        image=content,
    )
    print(f"Criado: {title}")
