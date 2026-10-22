import csv
import os
from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Book, Category, Loan, SearchQuery

LOAN_DAYS = 14
BOOKS_PER_PAGE = 10

ORDER_OPTIONS = {
    "title": ("Título (A–Z)", ["title"]),
    "author": ("Autor(a) (A–Z)", ["author", "title"]),
    "recent": ("Edição mais recente", ["-edition_year", "title"]),
    "available": ("Mais cópias disponíveis", ["-available", "title"]),
}

SEARCH_FIELDS = ["q", "title", "author", "publisher", "categoria", "idioma", "ano_min", "ano_max", "disponivel"]


def staff_required(view):
    """Decorator: só deixa passar quem está logado E faz parte da equipe."""

    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


def filter_books(params):
    """Aplica busca, filtros e ordenação."""
    books = Book.objects.select_related("category").annotate(
        available=F("copies_total") - Count("loans", filter=Q(loans__returned_at__isnull=True))
    )

    q = params.get("q", "").strip()
    if q:
        books = books.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(isbn__icontains=q))

    for field in ["title", "author", "publisher"]:
        value = params.get(field, "").strip()
        if value:
            books = books.filter(**{f"{field}__icontains": value})

    categoria = params.get("categoria", "")
    if categoria.isdigit():
        books = books.filter(category_id=int(categoria))

    idioma = params.get("idioma", "").strip()
    if idioma:
        books = books.filter(language__iexact=idioma)

    ano_min = params.get("ano_min", "")
    if ano_min.isdigit():
        books = books.filter(edition_year__gte=int(ano_min))

    ano_max = params.get("ano_max", "")
    if ano_max.isdigit():
        books = books.filter(edition_year__lte=int(ano_max))

    if params.get("disponivel") == "1":
        books = books.filter(available__gt=0)

    order_key = params.get("ordenar", "title")
    if order_key not in ORDER_OPTIONS:
        order_key = "title"
    _, order_fields = ORDER_OPTIONS[order_key]
    return books.order_by(*order_fields)


def filter_choices():
    return {
        "categories": Category.objects.all(),
        "languages": Book.objects.exclude(language="").values_list("language", flat=True).distinct().order_by("language"),
        "order_options": [(key, label) for key, (label, _) in ORDER_OPTIONS.items()],
    }


@login_required
def book_list(request):
    """Lista o acervo com busca, filtros, ordenação e paginação."""
    books = filter_books(request.GET)

    used = {key: request.GET[key] for key in SEARCH_FIELDS if request.GET.get(key)}
    if used and "page" not in request.GET:
        params = request.GET.dict()
        SearchQuery.objects.create(user=request.user, q=used.get("q", ""), params=params)

    paginator = Paginator(books, BOOKS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "params": request.GET,
        **filter_choices(),
    }
    return render(request, "catalog/book_list.html", context)


@login_required
def advanced_search(request):
    """Formulário completo de busca."""
    return render(request, "catalog/advanced_search.html", filter_choices())


@login_required
def search_history(request):
    """As últimas 50 buscas do usuário logado."""
    searches = request.user.searches.all()[:50]
    return render(request, "catalog/search_history.html", {"searches": searches})


@login_required
def book_pdf(request, book_id):
    """Abre o PDF do livro em modo inline para leitura no navegador."""
    book = get_object_or_404(Book, pk=book_id)
    if not book.pdf:
        raise Http404("PDF não disponível para este livro.")

    path = book.pdf.path
    if not os.path.exists(path):
        raise Http404("Arquivo PDF não encontrado.")

    response = FileResponse(open(path, "rb"), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{os.path.basename(path)}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
def export_books(request, file_format):
    """Baixa o resultado da busca atual em CSV ou Excel."""
    books = filter_books(request.GET)
    header = ["Título", "Autor(a)", "ISBN", "Categoria", "Idioma", "Ano", "Disponíveis", "Total"]
    rows = [
        [
            b.title,
            b.author,
            b.isbn,
            b.category.name if b.category else "",
            b.language,
            b.edition_year or "",
            b.available,
            b.copies_total,
        ]
        for b in books
    ]

    if file_format == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="livros.csv"'
        response.write("\ufeff")
        writer = csv.writer(response, delimiter=";")
        writer.writerow(header)
        writer.writerows(rows)
        return response

    if file_format == "xlsx":
        from openpyxl import Workbook

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Livros"
        sheet.append(header)
        for row in rows:
            sheet.append(row)
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="livros.xlsx"'
        workbook.save(response)
        return response

    raise Http404("Formato desconhecido.")


@login_required
def book_suggestions(request):
    """API para o autocompletar."""
    q = request.GET.get("q", "").strip()
    suggestions = []
    if len(q) >= 2:
        titles = Book.objects.filter(title__icontains=q).values_list("title", flat=True)[:5]
        authors = Book.objects.filter(author__icontains=q).values_list("author", flat=True).distinct()[:5]
        suggestions = list(dict.fromkeys([*titles, *authors]))
    return JsonResponse({"suggestions": suggestions})


@login_required
@require_POST
def borrow_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)

    if book.copies_available == 0:
        messages.error(request, f"Não há cópias disponíveis de “{book.title}”.")
        return redirect("catalog:book_list")

    already_has = book.loans.filter(user=request.user, returned_at__isnull=True).exists()
    if already_has:
        messages.warning(request, f"Você já está com “{book.title}”.")
        return redirect("catalog:book_list")

    due_date = timezone.localdate() + timedelta(days=LOAN_DAYS)
    Loan.objects.create(book=book, user=request.user, due_date=due_date)
    messages.success(request, f"Empréstimo feito! Devolva “{book.title}” até {due_date:%d/%m/%Y}.")
    return redirect("catalog:my_loans")


@login_required
def my_loans(request):
    loans = Loan.objects.filter(user=request.user).select_related("book")
    return render(request, "catalog/my_loans.html", {"loans": loans})


@login_required
@require_POST
def return_book(request, loan_id):
    loan = get_object_or_404(Loan, pk=loan_id, user=request.user)

    if loan.returned_at:
        messages.info(request, "Este livro já tinha sido devolvido.")
    else:
        loan.mark_returned()
        messages.success(request, f"“{loan.book.title}” devolvido. Obrigado!")
    return redirect("catalog:my_loans")


@staff_required
def overdue_loans(request):
    loans = (
        Loan.objects.filter(returned_at__isnull=True, due_date__lt=timezone.localdate())
        .select_related("book", "user")
        .order_by("due_date")
    )
    return render(request, "catalog/overdue_loans.html", {"loans": loans})


@staff_required
def book_borrowers(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    loans = book.loans.filter(returned_at__isnull=True).select_related("user")
    return render(request, "catalog/book_borrowers.html", {"book": book, "loans": loans})


@staff_required
@require_POST
def staff_mark_returned(request, loan_id):
    loan = get_object_or_404(Loan, pk=loan_id)
    if loan.is_active:
        loan.mark_returned()
        messages.success(request, f"Devolução de “{loan.book.title}” ({loan.user}) registrada.")
    return redirect("catalog:overdue_loans")
