from django.contrib import admin

from .models import Book, Category, Loan, SearchQuery


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "language", "edition_year", "copies_total", "copies_available")
    list_filter = ("category", "language")
    search_fields = ("title", "author", "isbn", "publisher")


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "borrowed_at", "due_date", "returned_at", "atrasado")
    list_filter = ("returned_at", "due_date")
    search_fields = ("book__title", "user__username")
    actions = ["marcar_como_devolvido"]

    @admin.display(boolean=True, description="Atrasado?")
    def atrasado(self, obj):
        return obj.is_overdue

    @admin.action(description="Marcar como devolvido")
    def marcar_como_devolvido(self, request, queryset):
        ativos = queryset.filter(returned_at__isnull=True)
        total = ativos.count()
        for loan in ativos:
            loan.mark_returned()
        self.message_user(request, f"{total} empréstimo(s) marcado(s) como devolvido(s).")


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ("user", "q", "created_at")
    list_filter = ("created_at",)
    search_fields = ("q", "user__username")