"""Configurações centrais: caminhos, modelos e parâmetros do vector store.

Os valores podem ser sobrescritos por variáveis de ambiente (ou pelo arquivo
``.env`` na raiz do projeto), sem alterar o código.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJ_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJ_ROOT / ".env")

# Caminhos
DATA_DIR = PROJ_ROOT / "data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REVIEWS_PATH = PROCESSED_DATA_DIR / "olist_reviews_com_metadados.csv"
VECTOR_STORE_DIR = Path(os.getenv("VECTOR_STORE_DIR", DATA_DIR / "vector_store"))

# Modelos Gemini
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# Vector store
COLLECTION_NAME = os.getenv("COLLECTION_NAME", f"olist_reviews_{EMBEDDING_DIM}d")
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))  # limite da API: 100
DEFAULT_TOP_K = 5
