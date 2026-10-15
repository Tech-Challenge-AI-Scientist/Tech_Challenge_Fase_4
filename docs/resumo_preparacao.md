# Preparação das avaliações — Tech Challenge Fase 4

## Fonte
Dataset: olistbr/brazilian-ecommerce, versão 2.
Arquivo: olist_order_reviews_dataset.csv.

## Seleção dos dados
- Base original: 99.224 avaliações.
- Título e comentário: 9.829.
- Somente comentário: 31.121.
- Somente título: 1.737.
- Sem título e sem comentário: 56.537.
- Base selecionada: 42.687 avaliações.

Foram mantidas avaliações com título ou comentário preenchido.
A amostra de títulos mostrou evidências úteis, como relatos sobre
prazo de entrega e não recebimento.
Registros sem texto nos dois campos ficaram fora do recorte textual.
Nenhum conteúdo foi inventado para preencher ausências.

## Limpeza dos textos
- Espaços repetidos, tabulações e quebras de linha foram
  padronizados para um único espaço.
- Espaços nas bordas foram removidos.
- Títulos alterados: 1.997.
- Comentários alterados: 11.475.
- Os textos originais foram preservados em colunas separadas.
- Acentos, números, pontuação, maiúsculas e negações foram mantidos.
- Não foram aplicados stemming, lematização ou remoção de stop words.
- Não foram encontradas tags ou entidades HTML nos títulos
  e comentários pelos padrões verificados.

## Avaliações e identificadores
- Foram identificados 146 pedidos com múltiplas avaliações
  na base textual selecionada.
- Avaliações distintas do mesmo pedido foram preservadas,
  pois podem conter informações complementares.
- Não foram encontradas linhas completamente duplicadas.
- review_id e order_id não apresentaram valores ausentes.
- 307 review_ids se repetem, envolvendo 624 linhas.
- O par review_id + order_id é único na base selecionada.
- Os dois identificadores devem ser preservados na próxima etapa.

## Notas e datas
- Todas as notas foram validadas no intervalo de 1 a 5.
- review_score foi convertido para inteiro no DataFrame.
- review_creation_date e review_answer_timestamp foram
  validados e convertidos para datetime.
- Não foram encontrados valores ausentes ou inválidos nesses campos.
- O CSV não preserva os tipos do pandas. Datas foram exportadas
  no formato YYYY-MM-DD HH:MM:SS.

## Validação final
- Avaliações preparadas: 42.687.
- Registros com título e comentário limpos simultaneamente vazios: 0.

## Entrega e uso
- Arquivo: olist_reviews_preparados.csv.
- Título preparado: review_comment_title_clean.
- Comentário preparado: review_comment_message_clean.
- Título e comentário permanecem separados.
- Organização dos documentos, embeddings, armazenamento
  e indexação pertencem à próxima etapa.

## Limitações
- O corpus representa apenas avaliações com conteúdo textual.
- A quantidade de avaliações não equivale à quantidade de pedidos.
- Textos genéricos, como elogios curtos, não foram excluídos.
- A limpeza de formatação não garante que todo texto contenha
  evidência útil; por exemplo, 'Não quero avaliar' requer atenção.
