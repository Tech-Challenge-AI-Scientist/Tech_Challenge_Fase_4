# Tech Challenge - Voice of Customer Intelligence com RAG

<a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10 ou superior" /></a>
<a href="https://pandas.pydata.org/" target="_blank"><img src="https://img.shields.io/badge/Pandas-2.2%2B-150458?logo=pandas&logoColor=white" alt="Pandas" /></a>
<a href="https://numpy.org/" target="_blank"><img src="https://img.shields.io/badge/NumPy-1.26%2B-013243?logo=numpy&logoColor=white" alt="NumPy" /></a>
<a href="https://matplotlib.org/" target="_blank"><img src="https://img.shields.io/badge/Matplotlib-Visualiza%C3%A7%C3%A3o-11557C" alt="Matplotlib" /></a>
<a href="https://github.com/Kaggle/kagglehub" target="_blank"><img src="https://img.shields.io/badge/KaggleHub-Data-20BEFF?logo=kaggle&logoColor=white" alt="KaggleHub" /></a>
<a href="https://ai.google.dev/gemini-api/docs" target="_blank"><img src="https://img.shields.io/badge/Google_Gemini-API-4285F4?logo=google&logoColor=white" alt="Google Gemini API" /></a>
<a href="https://www.trychroma.com/" target="_blank"><img src="https://img.shields.io/badge/ChromaDB-Vector_store-5B3CC4" alt="ChromaDB" /></a>
<a href="https://jupyter.org/" target="_blank"><img src="https://img.shields.io/badge/Jupyter-Notebooks-F37626?logo=jupyter&logoColor=white" alt="Jupyter" /></a>
<a href="https://pytest.org/" target="_blank"><img src="https://img.shields.io/badge/pytest-Tests-0A9EDC?logo=pytest&logoColor=white" alt="pytest" /></a>
<a href="https://python-dotenv.readthedocs.io/" target="_blank"><img src="https://img.shields.io/badge/python--dotenv-Config-1F6FEB" alt="python-dotenv" /></a>
<a href="https://tqdm.github.io/" target="_blank"><img src="https://img.shields.io/badge/tqdm-Progress-FFC107" alt="tqdm" /></a>
<a href="https://flake8.pycqa.org/" target="_blank"><img src="https://img.shields.io/badge/Flake8-PEP_8-315A9B" alt="Flake8" /></a>
<a href="https://black.readthedocs.io/" target="_blank"><img src="https://img.shields.io/badge/Black-Formatter-000000" alt="Black" /></a>

Projeto de inteligência de voz do cliente que combina recuperação semântica de avaliações de e-commerce com geração de respostas apoiadas em evidências. A base de conhecimento usa avaliações textuais da Olist enriquecidas com metadados de pedidos.

## Organização do projeto

```text
├── data/
│   ├── processed/                 # CSVs preparados e versionados
│   └── vector_store/              # índice persistido do ChromaDB; gerado localmente
├── docs/                          # resumos das etapas de preparação
├── notebooks/                     # exploração, preparação e construção do índice
├── tech_challenge_fase4/           # código Python do pipeline e da RAG
├── tests/                         # testes unitários sem chamadas à API Gemini
├── Makefile                       # atalhos para testes, índice e avaliação
├── pyproject.toml                 # metadados do pacote e dependências da aplicação
├── requirements.txt               # dependências de dados, desenvolvimento e pacote
└── README.md
```

## Reproduzir o RAG

Execute os passos abaixo na raiz do repositório. Os CSVs preparados já estão em `data/processed/`; portanto, para executar a RAG, não é necessário baixar novamente o dataset nem rodar os notebooks de preparação.

### 1. Criar e ativar o ambiente

O projeto requer Python 3.10 ou superior.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Instalar as dependências

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configurar a chave da API Gemini

Copie `.env.example` para `.env` e preencha `GEMINI_API_KEY` com uma chave criada no Google AI Studio. Não compartilhe nem versione o arquivo `.env`.

```powershell
# Windows (PowerShell)
Copy-Item .env.example .env
```

```bash
# Linux/macOS
cp .env.example .env
```

O código carrega `.env` automaticamente. A chave também pode ser definida diretamente como variável de ambiente.

### 4. (Opcional) Executar os testes

Os testes não chamam a API Gemini:

```bash
python -m pytest -q
```

### 5. Construir o vector store

O comando completo gera embeddings com o Gemini e persiste a coleção no ChromaDB em `data/vector_store/`:

```bash
python -m tech_challenge_fase4.vector_store
```

Para validar o fluxo com os primeiros 500 documentos antes de indexar a base completa:

```bash
python -m tech_challenge_fase4.vector_store --limite 500
```

A indexação é retomável: documentos já presentes na coleção são ignorados em execuções seguintes. `--recriar` apaga a coleção atual antes de indexar novamente. A pasta do vector store não é versionada.

### 6. Executar a RAG

```bash
python -m tech_challenge_fase4.rag
```

Digite uma pergunta no terminal. Para encerrar, digite `sair`, `exit` ou `quit`. Opções disponíveis:

| Opção | Descrição | Padrão |
|---|---|---:|
| `--k` | Avaliações recuperadas por pergunta | 30 |
| `--timeout` | Tempo limite de cada chamada ao Gemini, em segundos | 300 |
| `--debug` | Exibe logs detalhados, inclusive requisições HTTP | desativado |

Exemplo para recuperar 50 avaliações por pergunta:

```bash
python -m tech_challenge_fase4.rag --k 50
```

### 7. (Opcional) Avaliar a recuperação

Com o ambiente e a chave configurados, execute as consultas de avaliação:

```bash
python -m tech_challenge_fase4.avaliacao
```

No Linux/macOS, também estão disponíveis os atalhos `make test`, `make vector_store` e `make avaliar`.

## Sobre o projeto

A RAG responde perguntas sobre as avaliações dos clientes e pode relacionar os relatos a outros dados associados, como nota, prazo de entrega e categoria do pedido. A resposta deve usar somente o contexto recuperado, não inventar dados nem recorrer a conhecimento externo e informar quando o contexto não for suficiente. Cumprimentos e perguntas como "quem é você" são respondidos sem citar avaliações.

Exemplos de perguntas:

- Qual é o motivo mais frequente de insatisfação dos clientes?
- Em entregas bem avaliadas, quais são os elogios feitos com mais frequência?
- Qual é a nota média das avaliações?
- Quais são as categorias de produtos mais problemáticas?

## Etapas do projeto

### 1. Exploração e preparação das avaliações

O projeto utiliza o **Brazilian E-Commerce Public Dataset by Olist, versão 2**, com foco nos títulos e comentários das avaliações. A base original contém 99.224 avaliações; foram selecionadas 42.687 que têm título ou comentário preenchido.

| Notebook | Responsabilidade |
|---|---|
| `notebooks/Análise Exploratória.ipynb` | Exploração dos dados. |
| `notebooks/Limpeza_dados_Reviews.ipynb` | Seleção das avaliações com texto, limpeza e validação dos campos. |
| `notebooks/Preparacao_dados_complementares.ipynb` | Preparação de informações de pedidos e enriquecimento das avaliações. |

A limpeza padroniza espaços repetidos, tabulações e quebras de linha, e remove espaços nas bordas. Os textos originais são preservados; acentos, números, pontuação, maiúsculas e negações são mantidos. Não são aplicados stemming, lematização ou remoção de stop words. Nenhuma avaliação sem texto é preenchida artificialmente.

### 2. Preparar metadados dos pedidos

O notebook `notebooks/Preparacao_dados_complementares.ipynb` associa às avaliações informações de pedidos, localização, categorias e pagamentos. Foram preparados 99.441 pedidos e enriquecidas 42.687 avaliações, sem avaliações sem pedido correspondente. As junções preservaram a quantidade de avaliações e a unicidade do par `review_id` + `order_id`.

O atraso é calculado por dia para pedidos entregues com datas disponíveis. Entregas anteriores à compra ficam fora do cálculo, e atrasos desconhecidos permanecem ausentes em vez de serem tratados como zero ou falso. Categorias e pagamentos são agrupados por pedido; a categoria não é atribuída a um produto específico do comentário. Pedidos cancelados e avaliações sem correspondência não são excluídos automaticamente.

Os principais resultados em `data/processed/` são:

| Arquivo | Conteúdo |
|---|---|
| `olist_reviews_preparados.csv` | 42.687 avaliações com título ou comentário, textos originais e versões limpas. |
| `olist_orders_preparados.csv` | Dados de pedidos preparados. |
| `olist_metadados_pedidos.csv` | Informações de pedidos, localização, categorias e pagamentos, organizadas por pedido. |
| `olist_reviews_com_metadados.csv` | Avaliações preparadas associadas aos dados complementares; entrada do vector store. |

O CSV não preserva os tipos do pandas; datas são exportadas no formato `YYYY-MM-DD HH:MM:SS` e os tipos necessários devem ser definidos ao carregar. As oito tabelas adicionais foram disponibilizadas individualmente em `data/raw/`, sem tratamentos. Os CSVs preparados estão versionados e podem ser usados diretamente; os dados originais de `data/raw/` não são versionados.

Para reproduzir essa preparação, instale `kagglehub[pandas-datasets]` (já incluído em `requirements.txt`) e execute primeiro o notebook de limpeza dos reviews e depois o notebook de dados complementares, a partir de `notebooks/`. O carregamento usa `kagglehub` e reutiliza o cache local. Se for solicitada autenticação, use `kagglehub.login()` sem incluir credenciais no repositório.

As decisões, validações, resultados e limitações estão detalhadas em [resumo da preparação dos reviews](docs/resumo_preparacao.md) e [resumo da preparação dos dados complementares](docs/resumo_metadados.md).

### 3. Construir a base vetorial

O notebook `notebooks/2.0-construcao-vector-store.ipynb` percorre o mesmo fluxo de construção do índice passo a passo. No fluxo de código, `documentos.py` transforma cada linha em um documento cujo ID combina `review_id` e `order_id`; o texto contém título e comentário limpos, e os dados do pedido são metadados. Cada avaliação é um documento, sem chunking.

O modelo de embedding é `gemini-embedding-001`, com saída de 768 dimensões e tipos de tarefa distintos para documentos (`RETRIEVAL_DOCUMENT`) e perguntas (`RETRIEVAL_QUERY`). Os vetores são normalizados e gravados em uma coleção ChromaDB persistida localmente, usando distância de cosseno. O indexador envia documentos em lotes e pode retomar uma execução interrompida.

### 4. Recuperar e gerar respostas

Para cada pergunta, a aplicação gera um embedding, busca no ChromaDB as `k` avaliações mais similares e monta um contexto numerado. A resposta cita as avaliações por `[n]`; uma legenda relaciona cada número citado ao `review_id` e ao `order_id` reais. Por custo e desempenho, a geração usa uma amostra de tamanho `k`, não a base inteira; as contagens se referem à amostra recuperada.

Embeddings e geração usam a API Gemini. O projeto seleciona modelos da família Flash, descritos como relativamente baratos e eficazes para a tarefa, e o README anterior mencionava disponibilidade de free trial diária no Google AI Studio. Há uma divergência de configuração a observar: `tech_challenge_fase4/config.py` define `gemini-3.5-flash` como default do LLM, enquanto `.env.example` traz `LLM_MODEL=gemini-2.5-flash` comentado e a descrição anterior citava também versões 3.6, 3.7 e 3.8. O valor efetivo pode ser definido pela variável `LLM_MODEL`; confirme no Google AI Studio qual modelo está disponível para sua chave.

### 5. Avaliar

O módulo `avaliacao.py` executa consultas de teste e calcula precisão@k para a recuperação. Os testes unitários em `tests/` cobrem documentos, embeddings e vector store sem chamadas externas à API.

## Código e uso como biblioteca

| Módulo | Responsabilidade |
|---|---|
| `config.py` | Caminhos, modelos e parâmetros, com possibilidade de configuração por variáveis de ambiente. |
| `documentos.py` | Converte `olist_reviews_com_metadados.csv` em documentos e metadados. |
| `embeddings.py` | Cliente Gemini, envio em lotes, novas tentativas e normalização. |
| `vector_store.py` | Criação e indexação retomável no ChromaDB; também executável pela linha de comando. |
| `retriever.py` | Funções `buscar()` com filtros e `responder()` para uso como RAG. |
| `avaliacao.py` | Consultas de teste e precisão@k. |
| `rag.py` | Interface da RAG executável pelo terminal. |

Exemplo de uso:

```python
from tech_challenge_fase4.retriever import buscar, responder

buscar("atraso na entrega", k=5, filtros={"customer_state": "SP"})
buscar(
    "produto quebrado",
    filtros={"review_score": {"$lte": 2}, "entrega_atrasada": True},
)
responder("Quais as principais reclamações sobre entrega?")
```

Metadados disponíveis para filtro: `review_score`, `entrega_atrasada`, `dias_atraso`, `order_status`, `customer_state`, `customer_city`, `categoria_principal`, `categorias_pedido`, `formas_pagamento`, `valor_pago_pedido`, `review_ano_mes` (por exemplo, `201804`) e `tem_titulo`.

## Configuração

Além de `GEMINI_API_KEY`, podem ser definidos no `.env` ou no ambiente:

| Variável | Default em `config.py` |
|---|---|
| `EMBEDDING_MODEL` | `gemini-embedding-001` |
| `EMBEDDING_DIM` | `768` |
| `LLM_MODEL` | `gemini-3.5-flash` |
| `LLM_TEMPERATURE` | `0.2` |
| `VECTOR_STORE_DIR` | `data/vector_store` |
| `EMBEDDING_BATCH_SIZE` | `100` |

## Padronização do código (PEP 8)

O projeto usa **Black** para formatar automaticamente o código Python e **Flake8** para apontar problemas de estilo e qualidade. As dependências já estão em `requirements.txt`. A configuração do Flake8 em `setup.cfg` define o limite de 79 caracteres por linha, ignora `E203` e `W503` e exclui diretórios de dados, notebooks, referências e modelos.

Ative o ambiente virtual criado na etapa de instalação do RAG antes de executar as ferramentas:

```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source .venv/bin/activate
```

Para formatar os módulos e testes, incluindo a organização dos imports com isort:

```bash
python -m black tech_challenge_fase4 tests
python -m isort tech_challenge_fase4 tests
```

Para verificar o estilo sem alterar os arquivos:

```bash
python -m flake8 tech_challenge_fase4 tests
python -m isort --check --diff tech_challenge_fase4 tests
python -m black --check tech_challenge_fase4 tests
```

O comando `make format` aplica isort e Black; `make lint` executa Flake8, isort em modo de verificação e Black em modo de verificação. Esses atalhos requerem `make` disponível no sistema. No Windows, os comandos `python -m` acima podem ser usados diretamente no PowerShell.

Execute as verificações depois de alterar o código e aplique a formatação antes de compartilhar as mudanças.



