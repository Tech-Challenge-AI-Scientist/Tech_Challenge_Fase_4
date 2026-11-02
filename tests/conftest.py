import hashlib
import re

import numpy as np
import pandas as pd
import pytest

from tech_challenge_fase4.embeddings import normalizar


class FakeEmbedder:
    """Embedder determinístico (bag of words com hashing), sem chamar a API."""

    def __init__(self, dimensao: int = 64):
        self.dimensao = dimensao
        self.chamadas = 0

    def _vetor(self, texto: str) -> list[float]:
        v = np.zeros(self.dimensao)
        for palavra in re.findall(r"\w+", texto.lower()):
            v[int(hashlib.md5(palavra.encode()).hexdigest(), 16) % self.dimensao] += 1
        return v

    def embed_documentos(self, textos):
        self.chamadas += 1
        return normalizar([self._vetor(t) for t in textos])

    def embed_consulta(self, texto):
        return normalizar([self._vetor(texto)])[0]


@pytest.fixture
def embedder():
    return FakeEmbedder()


@pytest.fixture
def df_reviews():
    return pd.DataFrame(
        {
            "review_id": ["r1", "r2", "r3", "r3", "r5"],
            "order_id": ["o1", "o2", "o3", "o4", "o5"],
            "review_score": [1, 5, 2, 2, 4],
            "review_comment_title_clean": ["Atrasou", None, None, None, "Bom"],
            "review_comment_message_clean": [
                "produto chegou muito atrasado entrega demorada",
                "adorei chegou antes do prazo",
                "produto veio quebrado",
                "produto veio quebrado",
                None,
            ],
            "review_creation_date": ["2017-04-21 00:00:00"] * 5,
            "order_status": ["delivered"] * 5,
            "entrega_atrasada": [True, False, None, False, False],
            "dias_atraso": [5.0, -10.0, None, -2.0, -1.0],
            "customer_state": ["SP", "RJ", "SP", "SP", "MG"],
            "customer_city": ["sao paulo", "rio de janeiro", "campinas", "santos", "bh"],
            "categorias_pedido": ["bebes | cool_stuff", "esporte_lazer", None, "moveis", "artes"],
            "formas_pagamento": ["boleto"] * 5,
            "valor_pago_pedido": [100.0, 50.5, 20.0, 20.0, 10.0],
        }
    )
