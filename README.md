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
