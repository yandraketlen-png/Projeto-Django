"""
URL configuration for library project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Lista de endereços do projeto. O Django testa de cima para baixo e usa o primeiro que combinar.
urlpatterns = [
    # Painel administrativo: /admin/
    path("admin/", admin.site.urls),
    # Login, logout e recuperação de senha prontos do Django: /contas/login/, /contas/logout/ ...
    path("contas/", include("django.contrib.auth.urls")),
    # Todos os outros endereços são resolvidos pelo arquivo catalog/urls.py
    path("", include("catalog.urls")),
]

# Só em desenvolvimento (DEBUG=True): o próprio Django entrega as imagens enviadas (capas).
# Em um servidor de verdade, quem faz isso é o servidor web (Nginx, Apache...).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.urls import path

from . import views

# Namespace do app: nos templates escrevemos {% url 'catalog:book_list' %}
app_name = "catalog"

urlpatterns = [
    # Página inicial: lista de livros
    path("", views.book_list, name="book_list"),
    # <int:book_id> captura um número da URL e entrega para a view como book_id
    path("livros/<int:book_id>/emprestar/", views.borrow_book, name="borrow_book"),
    path("emprestimos/", views.my_loans, name="my_loans"),
    path("emprestimos/<int:loan_id>/devolver/", views.return_book, name="return_book"),
]