from django.core.management.base import BaseCommand

from catalog.models import Book, Category


class Command(BaseCommand):
    help = "Cria livros de exemplo para o acervo com capas e categorias"

    def handle(self, *args, **options):
        categories = {
            "Romance": "Obras clássicas e contemporâneas de ficção emocional.",
            "Tecnologia": "Livros sobre programação, ciência da computação e inovação.",
            "História": "Narrativas e estudos sobre povos, tempo e sociedade.",
            "Fantasia": "Mundos imaginários, magia e aventuras épicas.",
        }

        for name, description in categories.items():
            Category.objects.get_or_create(name=name, defaults={"description": description})

        books = [
            {
                "title": "Dom Casmurro",
                "author": "Machado de Assis",
                "isbn": "9788535910663",
                "category": "Romance",
                "language": "Português",
                "publisher": "Penguin Classics",
                "edition_year": 1899,
                "copies_total": 2,
                "synopsis": "Bento Santiago, o Dom Casmurro, revisita o passado e acompanha a dúvida que ronda sua vida: a traição de Capitu e a sombra de um passado que nunca se resolve. Uma obra sobre ciúmes, memória e a dúvida que acompanha a essência da vida humana.",
            },
            {
                "title": "Python Fluente",
                "author": "Luciano Ramalho",
                "isbn": "9788575224627",
                "category": "Tecnologia",
                "language": "Português",
                "publisher": "Novatec",
                "edition_year": 2015,
                "copies_total": 3,
                "synopsis": "Um guia completo para escrever código Python com estilo, clareza e eficiência. O livro explora a linguagem de forma prática, mostrando padrões, boas práticas e o uso inteligente das bibliotecas do ecossistema Python.",
            },
            {
                "title": "A Guerra do Fim do Mundo",
                "author": "Mario Vargas Llosa",
                "isbn": "9788535914067",
                "category": "História",
                "language": "Português",
                "publisher": "Alfaguara",
                "edition_year": 1981,
                "copies_total": 2,
                "synopsis": "Em uma trama intensa, o romance acompanha a formação de um movimento messiânico no sertão brasileiro e os conflitos entre utopia, poder e devoção. Uma narrativa profunda que explora a história e a ambiguidade dos sonhos políticos.",
            },
            {
                "title": "O Hobbit",
                "author": "J. R. R. Tolkien",
                "isbn": "9788595084756",
                "category": "Fantasia",
                "language": "Inglês",
                "publisher": "HarperCollins",
                "edition_year": 1937,
                "copies_total": 2,
                "synopsis": "Bilbo Bolseiro é convidado a uma jornada inesperada, onde aventura, coragem e amizade transformam uma vida pacata em uma grande história de descobertas. Uma fantasia clássica sobre coragem, mistério e o poder da jornada.",
            },
        ]

        for data in books:
            category = Category.objects.get(name=data.pop("category"))
            Book.objects.update_or_create(
                isbn=data["isbn"],
                defaults={**data, "category": category},
            )

        self.stdout.write(self.style.SUCCESS("Acervo popular com sucesso."))
