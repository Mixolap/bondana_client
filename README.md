# Bondana Client

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tinkoff-investments)](https://www.python.org/downloads/)

Обертка официального Tinkoff Invest API v2, оптимизированная для торговли обигациями на языке Python.



## Установка клиента

<!-- termynal -->

```
$ pip install tinkoff-investments

$ git clone https://github.com/Mixolap/bondana_client.git
```

## Как пользоваться

### Инициализация клиента

```python
from bondana_client.bondana_client import Bondana

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
```

### Постановка лимитной заявки

```python
# лимитная заявка на покупку
lots  = 1
price = 987.65
order_limit = client.orders.orders_limit_order_post(figi, 
	limit_order_request = {"lots": lots, "operation": "Buy", "price":price, "message": "custom_message",})  

# лимитная заявка на продажу
lots  = 1
price = 987.65
order_limit = client.orders.orders_limit_order_post(figi, 
	limit_order_request = {"lots": lots, "operation": "Sell", "price":price, "message": "custom_message",})                
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
	client.orders.orders_cancel_post(order["order_id"])
```
