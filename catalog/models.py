from urllib.parse import urlencode

from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    """Gênero ou assunto de um livro (Romance, Tecnologia, História...)."""

    name = models.CharField("Nome", max_length=100, unique=True)
    description = models.TextField("Descrição", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.name


class Book(models.Model):
    """Um título do acervo da biblioteca. Cada objeto vira uma linha da tabela catalog_book."""

    title = models.CharField("Título", max_length=255)
    author = models.CharField("Autor(a)", max_length=255)
    isbn = models.CharField("ISBN", max_length=13, unique=True)
    copies_total = models.PositiveIntegerField("Cópias totais", default=1)
    image = models.ImageField("Capa", upload_to="book_covers/", blank=True, null=True)
    pdf = models.FileField("PDF", upload_to="book_pdfs/", blank=True, null=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
        verbose_name="Categoria",
    )
    language = models.CharField("Idioma", max_length=50, blank=True, default="Português")
    publisher = models.CharField("Editora", max_length=150, blank=True)
    edition_year = models.PositiveSmallIntegerField("Ano de edição", null=True, blank=True)
    synopsis = models.TextField("Sinopse", blank=True, default="")

    created_at = models.DateTimeField("Cadastrado em", auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Livro"
        verbose_name_plural = "Livros"

    def __str__(self):
        return f"{self.title} — {self.author}"

    @property
    def copies_available(self):
        active_loans = self.loans.filter(returned_at__isnull=True).count()
        return max(self.copies_total - active_loans, 0)


class Loan(models.Model):
    """O empréstimo de um livro para um usuário. Um empréstimo nunca é apagado: ele é o histórico."""

    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="loans", verbose_name="Livro"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loans",
        verbose_name="Usuário",
    )
    borrowed_at = models.DateTimeField("Emprestado em", auto_now_add=True)
    due_date = models.DateField("Devolver até")
    returned_at = models.DateTimeField("Devolvido em", null=True, blank=True)

    class Meta:
        ordering = ["-borrowed_at"]
        verbose_name = "Empréstimo"
        verbose_name_plural = "Empréstimos"

    def __str__(self):
        status = "devolvido" if self.returned_at else "emprestado"
        return f"{self.book.title} para {self.user} ({status})"

    @property
    def is_active(self):
        return self.returned_at is None

    @property
    def is_overdue(self):
        return self.is_active and timezone.localdate() > self.due_date

    def mark_returned(self):
        if self.returned_at is None:
            self.returned_at = timezone.now()
            self.save(update_fields=["returned_at"])


class SearchQuery(models.Model):
    """Uma busca feita por um usuário, guardada para o histórico."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="searches",
        verbose_name="Usuário",
    )
    q = models.CharField("Texto buscado", max_length=255, blank=True)
    params = models.JSONField("Filtros usados", default=dict, blank=True)
    created_at = models.DateTimeField("Feita em", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Busca"
        verbose_name_plural = "Buscas"

    def __str__(self):
        return f"{self.user} buscou “{self.q or '(só filtros)'}”"

    def as_querystring(self):
        return urlencode(self.params)