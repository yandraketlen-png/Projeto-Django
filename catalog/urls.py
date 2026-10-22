from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.book_list, name="book_list"),
    path("busca-avancada/", views.advanced_search, name="advanced_search"),
    path("historico/", views.search_history, name="search_history"),
    path("exportar/<str:file_format>/", views.export_books, name="export_books"),
    path("livros/<int:book_id>/pdf/", views.book_pdf, name="book_pdf"),
    path("api/sugestoes/", views.book_suggestions, name="book_suggestions"),
    path("livros/<int:book_id>/emprestar/", views.borrow_book, name="borrow_book"),
    path("emprestimos/", views.my_loans, name="my_loans"),
    path("emprestimos/<int:loan_id>/devolver/", views.return_book, name="return_book"),
    path("equipe/atrasados/", views.overdue_loans, name="overdue_loans"),
    path("equipe/livros/<int:book_id>/leitores/", views.book_borrowers, name="book_borrowers"),
    path("equipe/emprestimos/<int:loan_id>/devolver/", views.staff_mark_returned, name="staff_mark_returned"),
]
