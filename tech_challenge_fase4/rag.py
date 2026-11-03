"""RAG de insights sobre as avaliações dos clientes, executado no terminal.

Uso::

    python -m tech_challenge_fase4.rag            # 30 avaliações por pergunta
    python -m tech_challenge_fase4.rag --k 50
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import time

import chromadb
from google import genai
from google.genai import errors, types

from tech_challenge_fase4 import config

logger = logging.getLogger(__name__)

INSTRUCAO_SISTEMA = """\
Você é um analista de experiência do cliente de um e-commerce brasileiro.
Sua tarefa é extrair insights de uma amostra de avaliações de clientes, respondendo
em português de forma clara, objetiva e precisa, baseando-se EXCLUSIVAMENTE nas
avaliações fornecidas no contexto.

Cada avaliação do contexto é identificada por um número entre colchetes, seguido da
nota (1 a 5), da situação da entrega e da categoria do produto.

Regras importantes:
- Nunca invente dados, números ou avaliações, nem use conhecimento externo.
- Utilize apenas as avaliações realmente relevantes para a pergunta e ignore as demais
  (ex.: elogios não entram em uma pergunta sobre insatisfação).
- Não seja literal ao interpretar as avaliações: clientes descrevem o mesmo problema com
  palavras diferentes (ex.: "não chegou", "nunca recebi" e "pedido sumiu" são o mesmo tema).
- Agrupe as avaliações em temas, ordene os temas pela quantidade de avaliações da amostra
  que os mencionam e informe essa quantidade (ex.: "7 de 30 avaliações").
- Cite os identificadores das avaliações de cada tema entre colchetes, ex.: [3], [12],
  sem repetir o mesmo identificador dentro de um tema.
- Deixe claro que as contagens se referem à amostra recuperada, não à base inteira.
- Se o contexto não for suficiente para responder, diga isso claramente.
- Limite a resposta a no máximo 3000 caracteres. Se houver muitos temas, priorize os
  mais frequentes e indique que existem outros de menor ocorrência.
- A resposta será exibida em um terminal: use texto simples, sem markdown (sem negrito,
  títulos ou tabelas), e sempre inicie os tópicos com "-".

Perguntas especiais:
- Em cumprimentos ou agradecimentos ("oi", "bom dia", "tudo bem?", "obrigado"),
  apenas responda educadamente.
- Se for perguntado quem você é ou qual é sua função, explique seu papel: analisar as
  avaliações dos clientes e responder perguntas sobre a experiência deles.
- Nas perguntas especiais, não cite nenhuma avaliação, mesmo que alguma tenha relação."""


def embed_pergunta(cliente: genai.Client, pergunta: str) -> list[float]:
    logger.info("Gerando embedding da pergunta (modelo %s)...", config.EMBEDDING_MODEL)
    inicio = time.perf_counter()
    resposta = cliente.models.embed_content(
        model=config.EMBEDDING_MODEL,
        contents=pergunta,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY", output_dimensionality=config.EMBEDDING_DIM
        ),
    )
    vetor = resposta.embeddings[0].values
    logger.info("Embedding gerado em %.2fs (dimensão %d).", time.perf_counter() - inicio, len(vetor))
    return vetor


def recuperar(
    cliente: genai.Client, colecao, pergunta: str, k: int
) -> list[tuple[str, str, dict]]:
    """Retorna tuplas (id do documento, texto, metadados); o id vem sempre no resultado."""
    vetor = embed_pergunta(cliente, pergunta)
    logger.info("Consultando o ChromaDB (k=%d)...", k)
    inicio = time.perf_counter()
    resultado = colecao.query(
        query_embeddings=[vetor],
        n_results=k,
        include=["documents", "metadatas"],
    )
    avaliacoes = list(
        zip(resultado["ids"][0], resultado["documents"][0], resultado["metadatas"][0])
    )
    logger.info(
        "%d avaliações recuperadas em %.2fs.", len(avaliacoes), time.perf_counter() - inicio
    )
    return avaliacoes


def montar_contexto(avaliacoes: list[tuple[str, str, dict]]) -> str:
    blocos = []
    for i, (_doc_id, texto, meta) in enumerate(avaliacoes, start=1):
        entrega = "entrega atrasada" if meta.get("entrega_atrasada") else "entrega no prazo"
        detalhes = f"nota {meta.get('review_score')}; {entrega}; {meta.get('categoria_principal')}"
        blocos.append(f"[{i}] ({detalhes})\n{texto}")
    return "\n\n".join(blocos)


def montar_legenda(texto: str, avaliacoes: list[tuple[str, str, dict]]) -> str:
    """Converte os números citados na resposta ([3], [3, 12]) nos ids reais da base."""
    citados = {
        int(n)
        for grupo in re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", texto)
        for n in re.findall(r"\d+", grupo)
    }
    linhas = []
    for n in sorted(citados):
        if 1 <= n <= len(avaliacoes):
            _doc_id, _texto, meta = avaliacoes[n - 1]
            linhas.append(
                f"[{n}] review_id={meta.get('review_id')} order_id={meta.get('order_id')}"
            )
        else:
            linhas.append(f"[{n}] (não pertence à amostra recuperada)")
    if not linhas:
        return ""
    return "Avaliações citadas:\n" + "\n".join(linhas)


def responder(cliente: genai.Client, colecao, pergunta: str, k: int) -> str:
    avaliacoes = recuperar(cliente, colecao, pergunta, k)
    if not avaliacoes:
        return "Nenhuma avaliação encontrada no vector store."

    prompt = (
        f"Amostra de {len(avaliacoes)} avaliações de clientes:\n\n"
        f"{montar_contexto(avaliacoes)}\n\n"
        f"Pergunta: {pergunta}"
    )
    logger.info(
        "Enviando prompt ao LLM (modelo %s, %d caracteres)...", config.LLM_MODEL, len(prompt)
    )
    inicio = time.perf_counter()
    resposta = cliente.models.generate_content(
        model=config.LLM_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCAO_SISTEMA, temperature=config.LLM_TEMPERATURE
        ),
    )
    logger.info("Resposta do LLM recebida em %.2fs.", time.perf_counter() - inicio)
    if not resposta.text:
        logger.warning("LLM retornou texto vazio. Resposta bruta: %s", resposta)
        return ""
    legenda = montar_legenda(resposta.text, avaliacoes)
    return f"{resposta.text.rstrip()}\n\n{legenda}" if legenda else resposta.text


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG de insights sobre as avaliações Olist.")
    parser.add_argument("--k", type=int, default=30, help="Avaliações recuperadas por pergunta.")
    parser.add_argument(
        "--timeout", type=int, default=300, help="Timeout (s) de cada chamada à API do Gemini."
    )
    parser.add_argument(
        "--debug", action="store_true", help="Exibe logs detalhados (inclui requisições HTTP)."
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if not args.debug:
        logging.getLogger("httpx").setLevel(logging.WARNING)

    api_key = os.getenv(config.GEMINI_API_KEY_ENV)
    if not api_key:
        raise SystemExit(f"Defina {config.GEMINI_API_KEY_ENV} no ambiente ou no arquivo .env.")
    logger.info("Criando cliente Gemini (timeout de %ds)...", args.timeout)
    cliente = genai.Client(
        api_key=api_key, http_options=types.HttpOptions(timeout=args.timeout * 1000)
    )

    logger.info(
        "Abrindo o ChromaDB em %s (coleção %s)...", config.VECTOR_STORE_DIR, config.COLLECTION_NAME
    )
    colecao = chromadb.PersistentClient(path=str(config.VECTOR_STORE_DIR)).get_collection(
        config.COLLECTION_NAME
    )
    print(f"{colecao.count()} avaliações carregadas. Digite 'sair' para encerrar.\n")

    while True:
        try:
            pergunta = input("Pergunta: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if pergunta.lower() in {"sair", "exit", "quit"}:
            break
        if not pergunta:
            continue
        logger.info("Pergunta recebida: %r", pergunta)
        inicio = time.perf_counter()
        try:
            print(f"\n{responder(cliente, colecao, pergunta, args.k)}\n")
        except errors.APIError as erro:
            print(f"\nErro na API do Gemini ({erro.code}): {erro.message}\n")
        except KeyboardInterrupt:
            print("\nPergunta cancelada.\n")
            continue
        except Exception:
            logger.exception("Erro inesperado ao responder a pergunta.")
            continue
        logger.info("Pergunta respondida em %.2fs.", time.perf_counter() - inicio)


if __name__ == "__main__":
    main()
