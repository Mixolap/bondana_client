# Bondana Client

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tinkoff-investments)](https://www.python.org/downloads/)

Неофициальная обертка официального Tinkoff Invest API v2, оптимизированная для торговли облигациями на языке Python.

> :warning: **На данный момент отлажена работа на облигациях номиналом 1000 рублей, на других номиналах не тестировалось**

## Установка клиента

<!-- termynal -->

```
$ pip install bondana-client

```

## Как пользоваться

### Инициализация клиента

```python
from bondana_client import Bondana

TOKEN = 'token'

client = Bondana(TOKEN)
```
 
### Получить баланс свободных денег в рублях 

```python
balance_rub, blocked = client.get_balance('rub')
```

### Получение списка бумаг в портфеле

```python
client.portfolio.portfolio_get()
for bond in portfolio.positions:
    print(bond)
```

### Получение истории операций

```python
from datetime import datetime, timedelta

nw = datetime.now() - timedelta(days=1) # получим сделки за последний день
d1 = datetime(nw.year, nw.month, nw.day, 0, 0, 0, tzinfo=timezone('Europe/Moscow'))  
d2 = datetime.now(tz=timezone('Europe/Moscow')) 

ops = client.operations.operations_get(limit=1000, from_=d1, to=d2)

ops.reverse()
for op in ops:
    print(op.get("figi"), op.get("price"), op.get("payment"), op.get("quantity"))

```

### Постановка лимитной заявки

```python
# лимитная заявка на покупку
lots  = 1
price = 987.65
figi = "BBG00Y9B45C2"
order_limit = client.orders.orders_limit_order_post(figi, 
	limit_order_request = {"lots": lots, "operation": "Buy", "price":price, })  

# лимитная заявка на продажу
lots  = 1
price = 997.65
figi = "BBG00Y9B45C2"
order_limit = client.orders.orders_limit_order_post(figi, 
	limit_order_request = {"lots": lots, "operation": "Sell", "price":price, })                
```

### Получение списка активных заявок

```python
client.orders.orders_get() # список заявок в формате объектов Tinkoff API
client.orders.orders_get_json() # список заявок в формате JSON

for order in client.orders.orders_get_json():
	print(order.get("order_id"), order.get("operation"), order.get("figi"))
```

### Отмена заявки на покупку

```python
# последовательная отмена всех активных заявок, для примера
for order in client.orders.orders_get_json():
	client.orders.orders_cancel_post(order.get("order_id"))
```

### Просмотр стакана по figi

```python
figi = "BBG00Y9B45C2"
orderbook = client.market.market_orderbook_get_dict(figi, 20)
```

### Получение списка всех доступных облигаций

```python
bonds = client.market.market_bonds_get()
for bond in bonds:
	print(bond)
```

## TODO:

получение лотности

шаг цены
