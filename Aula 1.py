"""Aula 1 - Introdução ao Django

1.1 O que é o Django
O Django é um framework web escrito em Python. Ele resolve problemas comuns de um sistema web
(banco de dados, login, segurança, formulários) e deixa para nós apenas o que é específico
do nosso sistema.

1.2 Como uma página é montada (padrão MTV)
Quando alguém acessa um endereço do sistema, o caminho é este:

Navegador                               Django
+----------+   1. pede /emprestimos/   +--------------+
|          | ------------------------> |  urls.py     |  "Qual função cuida deste endereço?"
|          |                           +------+-------+
|          |                                  v
|          |                           +--------------+   3. consulta   +--------------+
|          |                           |  VIEW        | ----------------> |  MODEL       | <- Banco de
|          |                           |  (views.py)  | <---------------- |  (models.py) |    dados
|          |                           +------+-------+   4. dados      +--------------+
|          |                                  v 5. entrega os dados
|          |   6. devolve o HTML       +--------------+
|          | <------------------------ |  TEMPLATE    |  "Monta o HTML com os dados"
+----------+                         |  (.html)     |
                                     +--------------+
"""

