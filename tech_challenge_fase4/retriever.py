"""Recuperação no vector store e geração de respostas com o Gemini.

Interface para o time do RAG::

    from tech_challenge_fase4.retriever import buscar, responder

    buscar("atraso na entrega", k=5, filtros={"customer_state": "SP"})
    buscar("produto quebrado", filtros={"review_score": {"$lte": 2}})
    responder("Quais as principais reclamações sobre entrega?")
"""

from __future__ import annotations

from functools import lru_cache

from tech_challenge_fase4 import config
from tech_challenge_fase4.embeddings import Embedder

INSTRUCAO_SISTEMA = (
    "Você é um analista de experiência do cliente de um e-commerce brasileiro. "
    "Responda em português usando SOMENTE as avaliações de clientes fornecidas no contexto. "
    "Se o contexto não for suficiente para responder, diga isso claramente. "
    "Ao afirmar algo, cite os identificadores das avaliações entre colchetes, ex.: [3]. "
    "Não invente dados, números ou avaliações."
)


@lru_cache(maxsize=1)
def _colecao_padrao():
    from tech_challenge_fase4.vector_store import obter_colecao

    return obter_colecao()


@lru_cache(maxsize=1)
def _embedder_padrao():
    from tech_challenge_fase4.embeddings import GeminiEmbedder

    return GeminiEmbedder()


def montar_where(filtros: dict | None) -> dict | None:
    """Converte ``{"campo": valor, ...}`` no formato ``where`` do Chroma.

    Valores podem ser literais (igualdade) ou operadores do Chroma, ex.:
    ``{"review_score": {"$lte": 2}}``. Vários campos são combinados com ``$and``.
    Um dicionário que já começa com ``$and``/``$or`` é repassado sem mudanças.
    """
    if not filtros:
        return None
    if any(chave.startswith("$") for chave in filtros):
        return filtros
    condicoes = [
        {campo: valor if isinstance(valor, dict) else {"$eq": valor}}
        for campo, valor in filtros.items()
    ]
    return condicoes[0] if len(condicoes) == 1 else {"$and": condicoes}


def buscar(
    consulta: str,
    k: int = config.DEFAULT_TOP_K,
    filtros: dict | None = None,
    colecao=None,
    embedder: Embedder | None = None,
) -> list[dict]:
    """Retorna as k avaliações mais similares à consulta.

    Cada item tem ``id``, ``texto``, ``metadados`` e ``similaridade`` (cosseno, 0–1).
    """
    colecao = colecao or _colecao_padrao()
    embedder = embedder or _embedder_padrao()

    resultado = colecao.query(
        query_embeddings=[embedder.embed_consulta(consulta)],
        n_results=k,
        where=montar_where(filtros),
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"id": id_, "texto": texto, "metadados": meta, "similaridade": round(1 - dist, 4)}
        for id_, texto, meta, dist in zip(
            resultado["ids"][0],
            resultado["documents"][0],
            resultado["metadatas"][0],
            resultado["distances"][0],
        )
    ]


def formatar_contexto(resultados: list[dict]) -> str:
    blocos = []
    for i, r in enumerate(resultados, start=1):
        m = r["metadados"]
        detalhes = [f"nota {m.get('review_score')}"]
        if "entrega_atrasada" in m:
            detalhes.append("entrega atrasada" if m["entrega_atrasada"] else "entrega no prazo")
        for campo in ("categoria_principal", "customer_state", "review_creation_date"):
            if campo in m:
                detalhes.append(str(m[campo]))
        blocos.append(f"[{i}] ({'; '.join(detalhes)})\n{r['texto']}")
    return "\n\n".join(blocos)


def responder(
    pergunta: str,
    k: int = 10,
    filtros: dict | None = None,
    colecao=None,
    embedder: Embedder | None = None,
    cliente=None,
    modelo: str = config.LLM_MODEL,
) -> dict:
    """RAG mínimo de referência: recupera avaliações e gera a resposta com o Gemini."""
    from google.genai import types

    from tech_challenge_fase4.embeddings import obter_cliente_gemini

    resultados = buscar(pergunta, k=k, filtros=filtros, colecao=colecao, embedder=embedder)
    if not resultados:
        return {
            "resposta": "Nenhuma avaliação encontrada para os filtros informados.",
            "fontes": [],
        }

    cliente = cliente or obter_cliente_gemini()
    prompt = (
        f"Avaliações de clientes:\n\n{formatar_contexto(resultados)}\n\n" f"Pergunta: {pergunta}"
    )
    resposta = cliente.models.generate_content(
        model=modelo,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCAO_SISTEMA, temperature=config.LLM_TEMPERATURE
        ),
    )
    return {"resposta": resposta.text, "fontes": resultados}
