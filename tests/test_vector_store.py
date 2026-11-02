from tech_challenge_fase4.documentos import construir_documentos
from tech_challenge_fase4.retriever import buscar, formatar_contexto, montar_where
from tech_challenge_fase4.vector_store import indexar, obter_colecao


def test_indexacao_retomavel(tmp_path, df_reviews, embedder):
    docs = construir_documentos(df_reviews)
    colecao = obter_colecao(tmp_path, "teste")

    assert indexar(docs[:2], colecao, embedder, tamanho_lote=1, mostrar_progresso=False) == 2
    # segunda execução só indexa o que falta
    assert indexar(docs, colecao, embedder, tamanho_lote=2, mostrar_progresso=False) == 3
    assert indexar(docs, colecao, embedder, mostrar_progresso=False) == 0
    assert colecao.count() == 5

    # persistência em disco
    assert obter_colecao(tmp_path, "teste").count() == 5
    assert obter_colecao(tmp_path, "teste", recriar=True).count() == 0


def test_buscar_com_filtros(tmp_path, df_reviews, embedder):
    colecao = obter_colecao(tmp_path, "teste")
    indexar(construir_documentos(df_reviews), colecao, embedder, mostrar_progresso=False)

    r = buscar("entrega atrasada", k=1, colecao=colecao, embedder=embedder)
    assert r[0]["id"] == "r1_o1"
    assert 0 < r[0]["similaridade"] <= 1

    r = buscar(
        "produto quebrado",
        k=5,
        filtros={"customer_state": "SP", "review_score": {"$lte": 2}},
        colecao=colecao,
        embedder=embedder,
    )
    assert {x["id"] for x in r} == {"r1_o1", "r3_o3", "r3_o4"}

    contexto = formatar_contexto(r)
    assert "[1]" in contexto and "nota" in contexto


def test_montar_where():
    assert montar_where(None) is None
    assert montar_where({"a": 1}) == {"a": {"$eq": 1}}
    assert montar_where({"a": 1, "b": {"$gte": 2}}) == {
        "$and": [{"a": {"$eq": 1}}, {"b": {"$gte": 2}}]
    }
    bruto = {"$or": [{"a": {"$eq": 1}}, {"b": {"$eq": 2}}]}
    assert montar_where(bruto) is bruto


def test_responder_usa_contexto_recuperado(tmp_path, df_reviews, embedder):
    from types import SimpleNamespace

    from tech_challenge_fase4.retriever import responder

    class LLMFalso:
        def __init__(self):
            self.models = self

        def generate_content(self, model, contents, config):
            self.prompt, self.config = contents, config
            return SimpleNamespace(text="resposta [1]")

    colecao = obter_colecao(tmp_path, "teste")
    indexar(construir_documentos(df_reviews), colecao, embedder, mostrar_progresso=False)
    llm = LLMFalso()
    saida = responder("entrega atrasada", k=2, colecao=colecao, embedder=embedder, cliente=llm)

    assert saida["resposta"] == "resposta [1]"
    assert len(saida["fontes"]) == 2
    assert "Pergunta: entrega atrasada" in llm.prompt and "[1]" in llm.prompt
    assert "SOMENTE" in llm.config.system_instruction


def test_avaliacao(tmp_path, df_reviews, embedder):
    from tech_challenge_fase4.avaliacao import ConsultaTeste, avaliar

    colecao = obter_colecao(tmp_path, "teste")
    indexar(construir_documentos(df_reviews), colecao, embedder, mostrar_progresso=False)
    consultas = [ConsultaTeste("entrega atrasada", lambda m: m["review_score"] <= 2, "nota baixa")]
    df = avaliar(k=1, consultas=consultas, colecao=colecao, embedder=embedder)
    assert df.loc[0, "precisao@1"] == 1.0
    assert df.loc[0, "top1"].startswith("Título: Atrasou")
