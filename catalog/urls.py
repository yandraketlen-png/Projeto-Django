from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.book_list, name="book_list"),
    path("livros/<int:book_id>/emprestar/", views.borrow_book, name="borrow_book"),
    path("emprestimos/", views.my_loans, name="my_loans"),
    path("emprestimos/<int:loan_id>/devolver/", views.return_book, name="return_book"),
]
