"""Avaliação da recuperação com consultas de teste.

Sem rótulos manuais, usamos os metadados como critério aproximado de
relevância (ex.: uma consulta sobre atraso deve trazer avaliações com
``entrega_atrasada=True`` ou nota baixa). Serve para comparar configurações
(dimensão do embedding, formato do texto) — não substitui a inspeção manual.

    python -m tech_challenge_fase4.avaliacao
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from tech_challenge_fase4 import config


@dataclass(frozen=True)
class ConsultaTeste:
    consulta: str
    relevante: Callable[[dict], bool]
    descricao: str
    filtros: dict | None = None


def _nota_baixa(m):
    return m.get("review_score", 5) <= 2


def _nota_alta(m):
    return m.get("review_score", 0) >= 4


CONSULTAS_TESTE = [
    ConsultaTeste(
        "pedido chegou atrasado, demorou muito para entregar",
        lambda m: m.get("entrega_atrasada") is True or _nota_baixa(m),
        "atrasada ou nota ≤ 2",
    ),
    ConsultaTeste("ainda não recebi o produto", _nota_baixa, "nota ≤ 2"),
    ConsultaTeste("produto veio quebrado, danificado", _nota_baixa, "nota ≤ 2"),
    ConsultaTeste("recebi o produto errado, diferente do anunciado", _nota_baixa, "nota ≤ 2"),
    ConsultaTeste("veio faltando itens no pedido", _nota_baixa, "nota ≤ 2"),
    ConsultaTeste("quero meu dinheiro de volta, cancelamento", _nota_baixa, "nota ≤ 2"),
    ConsultaTeste("produto de má qualidade, não recomendo", _nota_baixa, "nota ≤ 2"),
    ConsultaTeste(
        "chegou antes do prazo, entrega rápida",
        lambda m: m.get("entrega_atrasada") is False and _nota_alta(m),
        "no prazo e nota ≥ 4",
    ),
    ConsultaTeste("produto excelente, recomendo a loja", _nota_alta, "nota ≥ 4"),
    ConsultaTeste("bem embalado e conforme a descrição", _nota_alta, "nota ≥ 4"),
    ConsultaTeste("ótimo custo benefício", _nota_alta, "nota ≥ 4"),
    ConsultaTeste("atendimento do vendedor não responde", _nota_baixa, "nota ≤ 2"),
    ConsultaTeste(
        "reclamação de atraso na entrega",
        lambda m: m.get("customer_state") == "RJ",
        "filtro UF=RJ respeitado",
        filtros={"customer_state": "RJ"},
    ),
    ConsultaTeste(
        "produto com defeito",
        lambda m: m.get("review_score") == 1,
        "filtro nota=1 respeitado",
        filtros={"review_score": 1},
    ),
]


def avaliar(k: int = 10, consultas=CONSULTAS_TESTE, colecao=None, embedder=None) -> pd.DataFrame:
    from tech_challenge_fase4.retriever import buscar

    linhas = []
    for c in consultas:
        resultados = buscar(c.consulta, k=k, filtros=c.filtros, colecao=colecao, embedder=embedder)
        relevantes = sum(c.relevante(r["metadados"]) for r in resultados)
        linhas.append(
            {
                "consulta": c.consulta,
                "criterio": c.descricao,
                f"precisao@{k}": relevantes / max(len(resultados), 1),
                "similaridade_media": round(
                    sum(r["similaridade"] for r in resultados) / max(len(resultados), 1), 3
                ),
                "top1": resultados[0]["texto"].replace("\n", " | ") if resultados else "",
            }
        )
    return pd.DataFrame(linhas)


def main() -> None:
    pd.set_option("display.max_colwidth", 80)
    pd.set_option("display.width", 200)
    df = avaliar()
    print(df.to_string(index=False))
    print(f"\nPrecisão média: {df.filter(like='precisao').iloc[:, 0].mean():.2%}")
    print(
        f"Coleção: {config.COLLECTION_NAME} | modelo: {config.EMBEDDING_MODEL} ({config.EMBEDDING_DIM}d)"
    )


if __name__ == "__main__":
    main()
