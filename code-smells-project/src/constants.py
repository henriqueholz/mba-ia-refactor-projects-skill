"""Named constants — replaces magic numbers/strings scattered across the code.

Fixes AP-LOW-01 (magic numbers).
"""

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]

STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

NOME_MIN = 2
NOME_MAX = 200

# Faturamento discount tiers: (threshold, rate), highest first.
DISCOUNT_TIERS = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]
