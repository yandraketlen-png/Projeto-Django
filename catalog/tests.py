from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Book, Category, Loan, SearchQuery


def make_loan(book, user, days=14):
    return Loan.objects.create(book=book, user=user, due_date=timezone.localdate() + timedelta(days=days))


class LoanModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("maria", password="senha-forte-123")
        self.book = Book.objects.create(
            title="Dom Casmurro",
            author="Machado de Assis",
            isbn="9788535910663",
            copies_total=2,
        )

    def test_copies_available_desconta_emprestimos_ativos(self):
        self.assertEqual(self.book.copies_available, 2)
        make_loan(self.book, self.user)
        self.assertEqual(self.book.copies_available, 1)

    def test_emprestimo_com_prazo_vencido_esta_atrasado(self):
        loan = make_loan(self.book, self.user, days=-1)
        self.assertTrue(loan.is_overdue)

    def test_mark_returned_encerra_o_emprestimo(self):
        loan = make_loan(self.book, self.user)
        loan.mark_returned()
        self.assertFalse(loan.is_active)
        self.assertFalse(loan.is_overdue)
        self.assertEqual(self.book.copies_available, 2)


class BookListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("maria", password="senha-forte-123")
        self.client.force_login(self.user)
        Book.objects.create(title="Dom Casmurro", author="Machado de Assis", isbn="1111111111111")
        Book.objects.create(title="Capitães da Areia", author="Jorge Amado", isbn="2222222222222")

    def test_exige_login(self):
        self.client.logout()
        response = self.client.get(reverse("catalog:book_list"))
        self.assertEqual(response.status_code, 302)

    def test_busca_por_autor(self):
        response = self.client.get(reverse("catalog:book_list"), {"q": "machado"})
        self.assertContains(response, "Dom Casmurro")
        self.assertNotContains(response, "Capitães da Areia")

    def test_filtro_somente_disponiveis(self):
        livro = Book.objects.get(isbn="2222222222222")
        make_loan(livro, self.user)
        response = self.client.get(reverse("catalog:book_list"), {"disponivel": "1"})
        self.assertContains(response, "Dom Casmurro")
        self.assertNotContains(response, "Capitães da Areia")

    def test_paginacao_mostra_10_por_pagina(self):
        for i in range(15):
            Book.objects.create(title=f"Livro {i:02d}", author="Autor", isbn=f"99900000000{i:02d}")
        response = self.client.get(reverse("catalog:book_list"))
        self.assertEqual(len(response.context["page_obj"]), 10)
        self.assertContains(response, "Página 1 de 2")

    def test_modal_exibe_link_para_pdf_do_livro(self):
        livro = Book.objects.get(isbn="1111111111111")
        livro.pdf = SimpleUploadedFile("dom-casmurro.pdf", b"%PDF-1.4\n", content_type="application/pdf")
        livro.save()

        response = self.client.get(reverse("catalog:book_list"))
        self.assertContains(response, "Ler em PDF")
        self.assertContains(response, 'data-pdf="/livros/' )

    def test_pdf_abrir_em_formato_inline_no_navegador(self):
        livro = Book.objects.get(isbn="1111111111111")
        livro.pdf = SimpleUploadedFile("dom-casmurro.pdf", b"%PDF-1.4\n", content_type="application/pdf")
        livro.save()

        response = self.client.get(reverse("catalog:book_pdf", args=[livro.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("inline", response["Content-Disposition"])


class LoanViewsTests(TestCase):
    def setUp(self):
        self.maria = User.objects.create_user("maria", password="senha-forte-123")
        self.joao = User.objects.create_user("joao", password="senha-forte-123")
        self.book = Book.objects.create(
            title="Dom Casmurro",
            author="Machado de Assis",
            isbn="9788535910663",
            copies_total=1,
        )

    def test_emprestar_cria_emprestimo(self):
        self.client.force_login(self.maria)
        self.client.post(reverse("catalog:borrow_book", args=[self.book.id]))
        self.assertEqual(Loan.objects.filter(user=self.maria, book=self.book).count(), 1)

    def test_emprestar_exige_post(self):
        self.client.force_login(self.maria)
        response = self.client.get(reverse("catalog:borrow_book", args=[self.book.id]))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Loan.objects.count(), 0)

    def test_nao_empresta_sem_copias(self):
        make_loan(self.book, self.joao)
        self.client.force_login(self.maria)
        self.client.post(reverse("catalog:borrow_book", args=[self.book.id]))
        self.assertFalse(Loan.objects.filter(user=self.maria).exists())

    def test_nao_devolve_emprestimo_de_outra_pessoa(self):
        loan = make_loan(self.book, self.joao)
        self.client.force_login(self.maria)
        response = self.client.post(reverse("catalog:return_book", args=[loan.id]))
        self.assertEqual(response.status_code, 404)
        loan.refresh_from_db()
        self.assertTrue(loan.is_active)


class StaffViewsTests(TestCase):
    def setUp(self):
        self.leitor = User.objects.create_user("maria", password="senha-forte-123")
        self.equipe = User.objects.create_user("bibliotecaria", password="senha-forte-123", is_staff=True)
        self.book = Book.objects.create(
            title="Dom Casmurro",
            author="Machado de Assis",
            isbn="9788535910663",
        )

    def test_leitor_comum_recebe_403(self):
        self.client.force_login(self.leitor)
        response = self.client.get(reverse("catalog:overdue_loans"))
        self.assertEqual(response.status_code, 403)

    def test_equipe_ve_atrasados(self):
        make_loan(self.book, self.leitor, days=-3)
        self.client.force_login(self.equipe)
        response = self.client.get(reverse("catalog:overdue_loans"))
        self.assertContains(response, "Dom Casmurro")

    def test_equipe_registra_devolucao(self):
        loan = make_loan(self.book, self.leitor, days=-3)
        self.client.force_login(self.equipe)
        self.client.post(reverse("catalog:staff_mark_returned", args=[loan.id]))
        loan.refresh_from_db()
        self.assertFalse(loan.is_active)


class CatalogFiltersTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("maria", password="senha-forte-123")
        self.client.force_login(self.user)
        romance = Category.objects.create(name="Romance")
        tecnologia = Category.objects.create(name="Tecnologia")
        Book.objects.create(title="Dom Casmurro", author="Machado de Assis", isbn="1111111111111", category=romance, language="Português", edition_year=1899)
        Book.objects.create(title="Python Fluente", author="Luciano Ramalho", isbn="2222222222222", category=tecnologia, language="Português", edition_year=2015)
        Book.objects.create(title="Pride and Prejudice", author="Jane Austen", isbn="3333333333333", category=romance, language="Inglês", edition_year=1813)
        self.romance = romance

    def titles(self, response):
        return [book.title for book in response.context["page_obj"]]

    def test_filtro_por_categoria(self):
        response = self.client.get(reverse("catalog:book_list"), {"categoria": self.romance.id})
        self.assertEqual(self.titles(response), ["Dom Casmurro", "Pride and Prejudice"])

    def test_filtro_por_idioma_e_ano(self):
        response = self.client.get(reverse("catalog:book_list"), {"idioma": "português", "ano_min": "1900"})
        self.assertEqual(self.titles(response), ["Python Fluente"])

    def test_ordenar_por_edicao_mais_recente(self):
        response = self.client.get(reverse("catalog:book_list"), {"ordenar": "recent"})
        self.assertEqual(self.titles(response), ["Python Fluente", "Dom Casmurro", "Pride and Prejudice"])

    def test_busca_entra_no_historico(self):
        self.client.get(reverse("catalog:book_list"), {"q": "python"})
        busca = SearchQuery.objects.get(user=self.user)
        self.assertEqual(busca.q, "python")

    def test_abrir_a_lista_sem_filtros_nao_gera_historico(self):
        self.client.get(reverse("catalog:book_list"))
        self.assertEqual(SearchQuery.objects.count(), 0)

    def test_exportar_csv_respeita_os_filtros(self):
        response = self.client.get(reverse("catalog:export_books", args=["csv"]), {"q": "python"})
        conteudo = response.content.decode("utf-8")
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("Python Fluente", conteudo)
        self.assertNotIn("Dom Casmurro", conteudo)

    def test_exportar_excel(self):
        response = self.client.get(reverse("catalog:export_books", args=["xlsx"]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"PK"))

    def test_sugestoes_devolvem_json(self):
        response = self.client.get(reverse("catalog:book_suggestions"), {"q": "mach"})
        self.assertEqual(response.json(), {"suggestions": ["Machado de Assis"]})
