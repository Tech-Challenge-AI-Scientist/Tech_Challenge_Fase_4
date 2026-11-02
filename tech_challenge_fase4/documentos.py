"""Transforma as avaliações preparadas em documentos para o vector store.

Cada avaliação vira um único documento (os textos têm no máximo ~210
caracteres, então não há chunking). O texto embedado contém apenas título e
comentário; as demais informações do pedido vão como metadados, usados em
filtros na recuperação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path

import pandas as pd

from tech_challenge_fase4 import config

COLUNAS_OBRIGATORIAS = [
    "review_id",
    "order_id",
    "review_score",
    "review_comment_title_clean",
    "review_comment_message_clean",
]


@dataclass(frozen=True)
class Documento:
    id: str
    texto: str
    metadados: dict = field(default_factory=dict)


def carregar_reviews(caminho: Path | str = config.REVIEWS_PATH) -> pd.DataFrame:
    df = pd.read_csv(caminho, dtype={"review_id": str, "order_id": str})
    faltantes = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes em {caminho}: {faltantes}")
    return df


def _vazio(valor) -> bool:
    if valor is None:
        return True
    if isinstance(valor, float) and math.isnan(valor):
        return True
    return isinstance(valor, str) and not valor.strip()


def montar_texto(titulo, comentario) -> str:
    partes = []
    if not _vazio(titulo):
        partes.append(f"Título: {str(titulo).strip()}")
    if not _vazio(comentario):
        partes.append(f"Comentário: {str(comentario).strip()}")
    return "\n".join(partes)


def _bool_ou_none(valor):
    if _vazio(valor):
        return None
    if isinstance(valor, str):
        return valor.strip().lower() == "true"
    return bool(valor)


def _ano_mes(data) -> int | None:
    if _vazio(data):
        return None
    ts = pd.to_datetime(data, errors="coerce")
    return None if pd.isna(ts) else ts.year * 100 + ts.month


def montar_metadados(linha: dict) -> dict:
    """Metadados compatíveis com o Chroma (str, int, float, bool; sem nulos)."""
    categorias = linha.get("categorias_pedido")
    categoria_principal = None if _vazio(categorias) else str(categorias).split("|")[0].strip()

    dias_atraso = linha.get("dias_atraso")
    valor_pago = linha.get("valor_pago_pedido")

    metadados = {
        "review_id": linha["review_id"],
        "order_id": linha["order_id"],
        "review_score": int(linha["review_score"]),
        "tem_titulo": not _vazio(linha.get("review_comment_title_clean")),
        "review_creation_date": (
            None
            if _vazio(linha.get("review_creation_date"))
            else str(linha["review_creation_date"])
        ),
        "review_ano_mes": _ano_mes(linha.get("review_creation_date")),
        "order_status": linha.get("order_status"),
        "entrega_atrasada": _bool_ou_none(linha.get("entrega_atrasada")),
        "dias_atraso": None if _vazio(dias_atraso) else int(dias_atraso),
        "customer_state": linha.get("customer_state"),
        "customer_city": linha.get("customer_city"),
        "categorias_pedido": categorias,
        "categoria_principal": categoria_principal,
        "formas_pagamento": linha.get("formas_pagamento"),
        "valor_pago_pedido": None if _vazio(valor_pago) else float(valor_pago),
    }
    return {k: v for k, v in metadados.items() if not _vazio(v)}


def construir_documentos(df: pd.DataFrame) -> list[Documento]:
    """Gera um Documento por avaliação com texto não vazio.

    O id combina ``review_id`` e ``order_id``: o ``review_id`` sozinho se
    repete na base (há avaliações ligadas a mais de um pedido).
    """
    documentos = []
    for linha in df.to_dict(orient="records"):
        texto = montar_texto(
            linha.get("review_comment_title_clean"), linha.get("review_comment_message_clean")
        )
        if not texto:
            continue
        doc_id = f"{linha['review_id']}_{linha['order_id']}"
        documentos.append(Documento(id=doc_id, texto=texto, metadados=montar_metadados(linha)))

    ids = [d.id for d in documentos]
    if len(ids) != len(set(ids)):
        raise ValueError("Há ids de documento duplicados (review_id + order_id).")
    return documentos
