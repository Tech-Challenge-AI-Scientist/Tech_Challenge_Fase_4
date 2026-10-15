# Preparação dos metadados

Fonte: olistbr/brazilian-ecommerce/versions/2.
Pedidos preparados: 99441.
Reviews enriquecidos: 42687.
Reviews sem pedido correspondente: 0.

- Datas de pedidos validadas e convertidas.
- Atraso calculado por dia para pedidos entregues com datas disponíveis.
- Entregas anteriores à compra ficam fora do cálculo de atraso.
- Atraso desconhecido permanece ausente, não recebe zero ou falso.
- Cidade e UF associadas pelo customer_id.
- Categorias reunidas por pedido, sem atribuir o comentário a um produto específico.
- Formas e valores de pagamento agrupados por pedido.
- Sem exclusão automática de pedidos cancelados ou de reviews sem correspondência.
- Junção preservou a quantidade de avaliações e o par review_id/order_id.
- As oito tabelas adicionais foram exportadas individualmente em data/raw sem tratamentos.
- Geolocalização, vendedores e tradução de categorias não foram incorporados às junções.
- Campos de texto limpo dos reviews foram preservados.
- CSV não preserva tipos; definir os tipos necessários ao carregar.

Arquivos originais em data/raw:
- olist_orders_dataset.csv
- olist_customers_dataset.csv
- olist_order_items_dataset.csv
- olist_products_dataset.csv
- olist_order_payments_dataset.csv
- olist_sellers_dataset.csv
- olist_geolocation_dataset.csv
- product_category_name_translation.csv

Arquivos em data/processed:
- olist_orders_preparados.csv
- olist_metadados_pedidos.csv
- olist_reviews_com_metadados.csv
