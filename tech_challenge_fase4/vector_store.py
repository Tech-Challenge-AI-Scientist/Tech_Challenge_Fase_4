"""Construção e acesso ao vector store (ChromaDB persistido em disco).

Uso pela linha de comando::

    python -m tech_challenge_fase4.vector_store            # indexa tudo
    python -m tech_challenge_fase4.vector_store --limite 500   # amostra
    python -m tech_challenge_fase4.vector_store --recriar      # apaga e refaz

A indexação é retomável: documentos já presentes na coleção são ignorados,
então uma execução interrompida (ex.: limite da API) continua de onde parou.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

import chromadb

from tech_challenge_fase4 import config
from tech_challenge_fase4.documentos import (
    Documento,
    carregar_reviews,
    construir_documentos,
)
from tech_challenge_fase4.embeddings import Embedder

logger = logging.getLogger(__name__)


def obter_colecao(
    caminho: Path | str = config.VECTOR_STORE_DIR,
    nome: str = config.COLLECTION_NAME,
    recriar: bool = False,
):
    cliente = chromadb.PersistentClient(path=str(caminho))
    if recriar:
        try:
            cliente.delete_collection(nome)
        except Exception:  # coleção inexistente
            pass
    return cliente.get_or_create_collection(
        name=nome,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": config.EMBEDDING_MODEL,
            "embedding_dim": config.EMBEDDING_DIM,
        },
    )


def ids_existentes(colecao) -> set[str]:
    return set(colecao.get(include=[])["ids"])


def indexar(
    documentos: Sequence[Documento],
    colecao,
    embedder: Embedder,
    tamanho_lote: int = config.EMBEDDING_BATCH_SIZE,
    mostrar_progresso: bool = True,
) -> int:
    """Embeda e grava os documentos ainda ausentes da coleção. Retorna quantos gravou."""
    existentes = ids_existentes(colecao)
    pendentes = [d for d in documentos if d.id not in existentes]
    logger.info(
        "%d documentos no total, %d já indexados, %d pendentes.",
        len(documentos),
        len(documentos) - len(pendentes),
        len(pendentes),
    )

    lotes = range(0, len(pendentes), tamanho_lote)
    if mostrar_progresso:
        from tqdm.auto import tqdm

        lotes = tqdm(lotes, desc="Indexando", unit="lote")

    gravados = 0
    for inicio in lotes:
        lote = pendentes[inicio : inicio + tamanho_lote]
        vetores = embedder.embed_documentos([d.texto for d in lote])
        colecao.upsert(
            ids=[d.id for d in lote],
            embeddings=vetores,
            documents=[d.texto for d in lote],
            metadatas=[d.metadados for d in lote],
        )
        gravados += len(lote)
    return gravados


def construir_vector_store(
    limite: int | None = None, recriar: bool = False, embedder: Embedder | None = None
):
    if embedder is None:
        from tech_challenge_fase4.embeddings import GeminiEmbedder

        embedder = GeminiEmbedder()

    documentos = construir_documentos(carregar_reviews())
    if limite:
        documentos = documentos[:limite]
    colecao = obter_colecao(recriar=recriar)
    gravados = indexar(documentos, colecao, embedder)
    logger.info("Gravados nesta execução: %d. Total na coleção: %d.", gravados, colecao.count())
    return colecao


def main() -> None:
    parser = argparse.ArgumentParser(description="Constrói o vector store das avaliações Olist.")
    parser.add_argument(
        "--limite", type=int, default=None, help="Indexa só os N primeiros documentos."
    )
    parser.add_argument("--recriar", action="store_true", help="Apaga a coleção antes de indexar.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    construir_vector_store(limite=args.limite, recriar=args.recriar)


if __name__ == "__main__":
    main()
