"""Geração de embeddings com o Gemini (SDK ``google-genai``)."""

from __future__ import annotations

import logging
import os
import random
import time
from typing import Protocol, Sequence

import numpy as np

from tech_challenge_fase4 import config

logger = logging.getLogger(__name__)

# Erros transitórios: limite de requisições e indisponibilidade do serviço.
CODIGOS_REPETIVEIS = {429, 500, 502, 503, 504}


class Embedder(Protocol):
    dimensao: int

    def embed_documentos(self, textos: Sequence[str]) -> list[list[float]]: ...

    def embed_consulta(self, texto: str) -> list[float]: ...


def normalizar(vetores: Sequence[Sequence[float]]) -> list[list[float]]:
    """Normaliza em L2. Necessário para dimensões < 3072 no gemini-embedding-001."""
    matriz = np.asarray(vetores, dtype=np.float32)
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    normas[normas == 0] = 1.0
    return (matriz / normas).tolist()


def obter_cliente_gemini(api_key: str | None = None):
    from google import genai

    api_key = api_key or os.getenv(config.GEMINI_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(
            f"Defina a variável {config.GEMINI_API_KEY_ENV} (no ambiente ou no arquivo .env)."
        )
    return genai.Client(api_key=api_key)


class GeminiEmbedder:
    """Embeddings com ``task_type`` distinto para documentos e consultas."""

    def __init__(
        self,
        modelo: str = config.EMBEDDING_MODEL,
        dimensao: int = config.EMBEDDING_DIM,
        tamanho_lote: int = config.EMBEDDING_BATCH_SIZE,
        max_tentativas: int = 6,
        cliente=None,
    ):
        self.modelo = modelo
        self.dimensao = dimensao
        self.tamanho_lote = tamanho_lote
        self.max_tentativas = max_tentativas
        self.cliente = cliente or obter_cliente_gemini()

    def _chamar_api(self, textos: Sequence[str], task_type: str) -> list[list[float]]:
        from google.genai import errors, types

        cfg = types.EmbedContentConfig(task_type=task_type, output_dimensionality=self.dimensao)
        for tentativa in range(1, self.max_tentativas + 1):
            try:
                resposta = self.cliente.models.embed_content(
                    model=self.modelo, contents=list(textos), config=cfg
                )
                return normalizar([e.values for e in resposta.embeddings])
            except errors.APIError as erro:
                if erro.code not in CODIGOS_REPETIVEIS or tentativa == self.max_tentativas:
                    raise
                espera = min(60, 2**tentativa) + random.uniform(0, 1)
                logger.warning(
                    "Erro %s na API (tentativa %d/%d). Nova tentativa em %.0fs.",
                    erro.code,
                    tentativa,
                    self.max_tentativas,
                    espera,
                )
                time.sleep(espera)
        raise RuntimeError("Número máximo de tentativas excedido.")

    def embed_documentos(self, textos: Sequence[str]) -> list[list[float]]:
        vetores = []
        for i in range(0, len(textos), self.tamanho_lote):
            vetores.extend(
                self._chamar_api(textos[i : i + self.tamanho_lote], "RETRIEVAL_DOCUMENT")
            )
        return vetores

    def embed_consulta(self, texto: str) -> list[float]:
        return self._chamar_api([texto], "RETRIEVAL_QUERY")[0]
