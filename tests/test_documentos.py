from tech_challenge_fase4.config import REVIEWS_PATH
from tech_challenge_fase4.documentos import (
    carregar_reviews,
    construir_documentos,
    montar_texto,
)


def test_montar_texto():
    assert montar_texto("Ótimo", "chegou rápido") == "Título: Ótimo\nComentário: chegou rápido"
    assert montar_texto(None, "chegou rápido") == "Comentário: chegou rápido"
    assert montar_texto(float("nan"), "  ") == ""


def test_construir_documentos(df_reviews):
    docs = construir_documentos(df_reviews)
    assert len(docs) == 5
    # review_id repetido gera ids distintos graças ao order_id
    assert {d.id for d in docs} >= {"r3_o3", "r3_o4"}
    d1 = docs[0]
    assert d1.metadados["review_score"] == 1
    assert d1.metadados["entrega_atrasada"] is True
    assert d1.metadados["dias_atraso"] == 5
    assert d1.metadados["categoria_principal"] == "bebes"
    assert d1.metadados["review_ano_mes"] == 201704
    # nenhum metadado nulo (exigência do Chroma)
    for d in docs:
        assert all(v is not None for v in d.metadados.values())
    assert "entrega_atrasada" not in docs[2].metadados


def test_base_real_gera_um_documento_por_review():
    df = carregar_reviews(REVIEWS_PATH)
    docs = construir_documentos(df)
    assert len(docs) == len(df) == 42687
    assert max(len(d.texto) for d in docs) < 300
