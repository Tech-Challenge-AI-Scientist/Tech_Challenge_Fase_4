# project_name

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

A short description of the project.

## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         project_name and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── project_name   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes project_name a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

## Preparação dos dados

A preparação utiliza o **Brazilian E-Commerce Public Dataset by Olist, versão 2**, com foco nos títulos e comentários das avaliações.

| Notebook | Responsabilidade |
|---|---|
| `notebooks/Limpeza_dados_Reviews.ipynb` | Seleção das avaliações com conteúdo textual, limpeza dos textos e validação dos campos. |
| `notebooks/Preparacao_dados_complementares.ipynb` | Preparação de informações dos pedidos e enriquecimento das avaliações. |

### Resultados gerados

Os arquivos estão em `data/processed/`:

| Arquivo | Conteúdo |
|---|---|
| `olist_reviews_preparados.csv` | **42.687 avaliações** com título ou comentário preenchido, incluindo os textos originais e suas versões limpas. |
| `olist_metadados_pedidos.csv` | Informações de pedidos, localização, categorias e pagamentos, organizadas por pedido. |
| `olist_reviews_com_metadados.csv` | Avaliações preparadas associadas aos dados complementares. |

As junções preservaram as **42.687 avaliações**. O par `review_id` + `order_id` foi validado como único nessa base.

### Reprodução

Instale a dependência de acesso ao dataset:

```bash
pip install "kagglehub[pandas-datasets]"
```

Execute primeiro o notebook de limpeza dos reviews e depois o de dados complementares, a partir da pasta `notebooks/`.

O carregamento é feito pelo `kagglehub`, com reutilização do cache local. Caso seja solicitada autenticação, utilize `kagglehub.login()` sem incluir credenciais no repositório.

### Documentação

As decisões de tratamento, validações, resultados e limitações estão documentadas nos notebooks e nos arquivos:

- [Resumo da preparação dos reviews](docs/resumo_preparacao.md)
- [Resumo da preparação dos dados complementares](docs/resumo_metadados.md)

As oito tabelas adicionais foram disponibilizadas separadamente em `data/raw/`, sem tratamentos.

> Os CSVs preparados estão versionados em `data/processed/` e podem ser utilizados diretamente. Os dados originais de `data/raw/` não são versionados; podem ser obtidos pelo `kagglehub`, conforme o carregamento dos notebooks.

## Base de conhecimento (vector store) e LLM

Embeddings e geração usam o **Gemini**. Os vetores ficam no **ChromaDB**, persistido em `data/vector_store/`. Essa pasta não é versionada e pode ser gerada de novo a qualquer momento.

| Componente | Escolha |
|---|---|
| Embeddings | `gemini-embedding-001` (768 dimensões) |
| LLM | `gemini-2.5-flash` |
| Vector store | ChromaDB, distância de cosseno |
| Unidade | 1 avaliação = 1 documento (sem chunking), com os dados do pedido como metadados |

## RAG (Retrieval-Augmented Generation)

A RAG tem como função responder perguntas a respeito das avaliações feitas pelos clientes. Além de analisar as avaliações, a RAG também é capaz de gerar insights a respeito de outros dados das mesmas, como a nota da avaliação e a categoria dos produtos. A RAG não usa conhecimento externo nem inventa dados, avisando quando o contexto não basta para responder. Cumprimentos e perguntas do tipo "quem é você" são respondidos sem citar avaliações.

Alguns exemplos de perguntas que podem ser feitas à RAG são:

- Qual é o motivo mais frequente de insatisfação dos clientes?
- Em entregas bem avaliadas, quais são os elogios feitos com mais frequência?
- Qual é a nota média das avaliações?
- Quais são as categorias de produtos mais problemáticas?

#### Modelo

A RAG utiliza os modelos da família flash do Gemini, por serem modelos relativamente baratos (além de contarem com uma free trial diária no Google AI Studio) e muito eficazes nesta tarefa em específico. Por padrão, está configurado o modelo gemini-3.5-flash, porém, pode ser substituído por outras versões do mesmo, como a 3.6, 3.7 e 3.8.

#### Funcionamento

1. A pergunta vira um embedding (RETRIEVAL_QUERY, 768 dimensões).
2. As k avaliações mais parecidas são buscadas no ChromaDB.
3. O contexto é montado com as avaliações numeradas por [n], cada uma com nota, situação da entrega e categoria. A resposta cita as avaliações como [n], e no final aparece uma legenda que liga cada número ao review_id e ao order_id reais.

Obs: Por fins de custo e performance, a RAG utiliza apenas uma amostra (k) das avaliações. Na sessão "executando a RAG", é possível verificar como alterar o número de avaliações recuperadas.

#### Executando a RAG

Antes de executar, é necessário configurar a variável de ambiente GEMINI_API_KEY com a sua chave de API do Gemini, chave esta que é configurável pelo painel do Google AI Studio.

```bash
python -m tech_challenge_fase4.rag
```

Opcionalmente, podem ser configurados os seguintes parâmetros:

- --k: quantas avaliações são recuperadas por pergunta (padrão 30).
- --timeout: tempo limite de cada chamada ao Gemini (padrão 300 s).
- --debug: mostra logs detalhados, inclusive as requisições HTTP.

Para encerrar a sessão, basta digitar "sair", "exit" ou "quit".


### Código (`tech_challenge_fase4/`)

| Módulo | Responsabilidade |
|---|---|
| `config.py` | Caminhos, modelos e parâmetros (podem ser alterados por variáveis de ambiente) |
| `documentos.py` | Converte `olist_reviews_com_metadados.csv` em documentos e metadados |
| `embeddings.py` | Cliente Gemini, envio em lotes, novas tentativas e normalização |
| `vector_store.py` | Criação e indexação retomável no ChromaDB (também funciona pela linha de comando) |
| `retriever.py` | `buscar()` com filtros e `responder()` (RAG de referência) |
| `avaliacao.py` | Consultas de teste e precisão@k |
| `rag.py` | Script da RAG, executável via terminal |

### Como gerar

#### Linux
```bash
python -m venv .venv            # criar o ambiente virtual (uma vez só)
source .venv/bin/activate       # ativa o ambiente
pip install -r requirements.txt # instala as dependências
cp .env.example .env            # preencha GEMINI_API_KEY
make test                       # testes sem chamar a API
python -m tech_challenge_fase4.vector_store --limite 500   # amostra
make vector_store               # base completa (retomável)
make avaliar                    # avaliação da recuperação
```

#### Windows
```bash
python -m venv .venv            # criar o ambiente virtual (uma vez só)
.\.venv\Scripts\Activate.ps1    # ativa o ambiente
pip install -r requirements.txt # instala as dependências
cp .env.example .env            # preencha GEMINI_API_KEY
python -m tech_challenge_fase4.test                       # testes sem chamar a API
python -m tech_challenge_fase4.vector_store --limite 500  # amostra
python -m tech_challenge_fase4.vector_store               # base completa (retomável)
python -m tech_challenge_fase4.avaliacao                  # avaliação da recuperação
```

O notebook `notebooks/2.0-construcao-vector-store.ipynb` executa o mesmo fluxo passo a passo.

### Uso pelo RAG

```python
from tech_challenge_fase4.retriever import buscar, responder

buscar("atraso na entrega", k=5, filtros={"customer_state": "SP"})
buscar("produto quebrado", filtros={"review_score": {"$lte": 2}, "entrega_atrasada": True})
responder("Quais as principais reclamações sobre entrega?")
```

Metadados disponíveis para filtro: `review_score`, `entrega_atrasada`, `dias_atraso`, `order_status`, `customer_state`, `customer_city`, `categoria_principal`, `categorias_pedido`, `formas_pagamento`, `valor_pago_pedido`, `review_ano_mes` (ex.: `201804`), `tem_titulo`.

--------

