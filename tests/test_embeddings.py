from types import SimpleNamespace

from google.genai import errors
import numpy as np
import pytest

from tech_challenge_fase4 import embeddings
from tech_challenge_fase4.embeddings import GeminiEmbedder, normalizar


class ClienteFalso:
    """Imita client.models.embed_content; falha nas primeiras chamadas se pedido."""

    def __init__(self, falhas=0, codigo=429):
        self.falhas, self.codigo, self.chamadas = falhas, codigo, []
        self.models = self

    def embed_content(self, model, contents, config):
        self.chamadas.append((model, list(contents), config))
        if self.falhas:
            self.falhas -= 1
            raise errors.APIError(self.codigo, {"error": {"message": "falha simulada"}})
        vetor = [3.0] + [4.0] + [0.0] * (config.output_dimensionality - 2)
        return SimpleNamespace(embeddings=[SimpleNamespace(values=vetor) for _ in contents])


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr(embeddings.time, "sleep", lambda s: None)


def test_normalizar():
    v = normalizar([[3, 4], [0, 0]])
    assert np.allclose(v[0], [0.6, 0.8]) and v[1] == [0.0, 0.0]


def test_lotes_task_type_e_normalizacao():
    cliente = ClienteFalso()
    emb = GeminiEmbedder(modelo="m", dimensao=8, tamanho_lote=2, cliente=cliente)
    vetores = emb.embed_documentos(["a", "b", "c"])
    assert len(vetores) == 3 and len(vetores[0]) == 8
    assert np.isclose(np.linalg.norm(vetores[0]), 1.0)
    assert [len(c[1]) for c in cliente.chamadas] == [2, 1]
    assert cliente.chamadas[0][2].task_type == "RETRIEVAL_DOCUMENT"

    emb.embed_consulta("q")
    assert cliente.chamadas[-1][2].task_type == "RETRIEVAL_QUERY"


def test_repete_em_limite_de_taxa():
    cliente = ClienteFalso(falhas=2, codigo=429)
    GeminiEmbedder(dimensao=4, cliente=cliente).embed_consulta("q")
    assert len(cliente.chamadas) == 3


def test_nao_repete_erro_permanente():
    cliente = ClienteFalso(falhas=1, codigo=400)
    with pytest.raises(errors.APIError):
        GeminiEmbedder(dimensao=4, cliente=cliente).embed_consulta("q")
    assert len(cliente.chamadas) == 1


def test_exige_chave(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        embeddings.obter_cliente_gemini()
