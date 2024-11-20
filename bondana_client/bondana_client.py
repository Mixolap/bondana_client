import math

from datetime import datetime, timezone, timedelta

from tinkoff.invest import Client, GetOperationsByCursorRequest, Quotation
from tinkoff.invest.constants import INVEST_GRPC_API


DEFAULT_BOND_NOMINAL = 1000 # https://tinkoff.github.io/investAPI/head-marketdata/ В сервисе TINKOFF INVEST API для отображения цен облигаций и фьючерсов используются пункты. Для облигаций один пункт равен одному проценту номинала облигации

OPERATION_STATE_EXECUTED = 1

INSTRUMENT_STATUS_BASE = 1

def getInstrumentType(v):
    if v==0: return ""
    if v==1: return "Bond"
    if v==3: return "Currency"
    raise Exception("unknown operation type", v)


def cast_count(v):
    return v.units


def cast_money(v):
    return v.units + v.nano / 1e9 #


def dateToString(v):
    return v.astimezone(timezone(timedelta(hours=3), 'Europe/Moscow')).strftime('%Y-%m-%d %H:%M:%S.%f')


def cast_to_bond_price(v):
    price = v
    units = math.floor(price)
    nano = math.floor((price-units) * 1e9 + 0.1)
    return Quotation(units=units, nano=nano)


class OrdersApi(object):
    token = None
    account = None
    def __init__(self, token, account):
        self.token = token
        self.account = account
    
    def orders_get(self):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            data = client.orders.get_orders(account_id=self.account.id)
            return data.orders

    def orders_get_json(self):
        return [{
            "figi": order.figi,
            "operation": "Buy" if order.direction==1 else "Sell",
            "price": cast_money(order.initial_order_price)/order.lots_requested,
            "order_id": order.order_id,
            "requested_lots": order.lots_requested,
            "executed_lots": order.lots_executed,
            # "object": order,
        } for order in self.orders_get()]

    def orders_limit_order_post(self, figi, limit_order_request):
        quantity = limit_order_request["lots"]
        price = cast_to_bond_price(limit_order_request["price"])
        direction = 1 if limit_order_request["operation"]=="Buy" else 2 # 1 - покупка 2 - продажа
        order_type = 1 # 1 - лимитная 2 - рыночная
        order_id=limit_order_request.get("order_id", str(datetime.utcnow().timestamp()))
        with Client(self.token, target=INVEST_GRPC_API) as client:
            data = client.orders.post_order(account_id=self.account.id, instrument_id=figi, quantity=quantity, price=price, direction=direction, order_type=order_type, order_id=order_id)
            return data

    def orders_cancel_post(self, order_id):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            if isinstance(order_id, str):
                data = client.orders.cancel_order(account_id=self.account.id, order_id=order_id)
            else:
                for order in order_id:
                    data = client.orders.cancel_order(account_id=self.account.id, order_id=order)
            return data


class OperationsApi(object):
    def __init__(self, token, account):
        self.account = account
        self.token = token

    def getOperationState(self, v):
        if v==1:
            return "Done"
        raise Exception("unknown operation state", v)

    def getOperationType(self, v):
        if v==0: return "UNSPECIFIED"
        if v==1: return "PayIn"
        if v==2: return "Tax"        
        if v==5: return "Tax"
        if v==6: return "Repayment"
        if v==11: return "TaxCorrection"
        if v==9: return "PayOut"
        if v==10: return "PartRepayment"
        if v==12: return "ServiceCommission"
        if v==15: return "Buy"
        if v==19: return "BrokerCommission"
        if v==22: return "Sell"
        if v==23: return "Coupon"
        if v==25: return "OPERATION_TYPE_DIVIDEND_TRANSFER"
        if v==60: return "OPERATION_TYPE_INP_MULTI"
        if v==61: return "OPERATION_TYPE_OVER_PLACEMENT"
        if v==62: return "OPERATION_TYPE_OVER_COM"
        raise Exception("unknown operation type", v)

    def operationToJson(self, op):
        # if dateToString(op.date)==None:
        operation_id = op.id
        if self.getOperationType(op.type)=="Coupon":
            operation_id=op.date.strftime('%Y%m%d%H%M%S')
        if op.type==22 and op.figi=='':
            print("BONDANA NO FIGI", op)
        return {
            "broker_account_id": op.broker_account_id,
            "id": operation_id,
            "name": op.name,
            "date": dateToString(op.date),
            "figi": op.figi,
            "price": cast_money(op.price),
            "status": self.getOperationState(op.state),
            "trades": [{"date": dateToString(d.date), "price": cast_money(d.price), "quantity": d.quantity} for d in op.trades_info.trades],
            "payment": cast_money(op.payment),
            "currency": op.payment.currency.upper(),
            "quantity": op.quantity_done,
            "commission":{"value": cast_money(op.commission), "currency": op.commission.currency.upper()},
            "operation_type": self.getOperationType(op.type),
            "instrument_type": getInstrumentType(op.instrument_kind),
        }        

    def operations_get(self, from_, to, limit):
        def get_request(cursor, from_, to, limit):
            return GetOperationsByCursorRequest(account_id=self.account.id, from_=from_, to=to, limit=limit, state=OPERATION_STATE_EXECUTED, cursor=cursor)
        with Client(self.token, target=INVEST_GRPC_API) as client:
            operations = client.operations.get_operations_by_cursor(get_request("", from_, to, limit))
            # print(operations)
            return [self.operationToJson(op) for op in operations.items]


class PortfolioApi(object):
    def __init__(self, token, account):
        self.account = account
        self.token = token

    def portfolio_get(self):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            portfolio = client.operations.get_portfolio(account_id=self.account.id)
            return portfolio

    def portfolio_currencies_get(self):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            limits = client.operations.get_withdraw_limits(account_id=self.account.id)
            return limits


class MarketApi(object):
    def __init__(self, token, account):
        self.account = account
        self.token = token

    def market_orderbook_get_dict(self, figi, depth, bond_nominal=DEFAULT_BOND_NOMINAL):
        o = self.market_orderbook_get(figi, depth)
        bond_nominal = bond_nominal/100.
        return {
            "figi": o.figi,
            "depth": o.depth,
            "bids": [{"price": round(cast_money(d.price)*bond_nominal, 7), "quantity": d.quantity} for d in o.bids],
            "asks": [{"price": round(cast_money(d.price)*bond_nominal, 7), "quantity": d.quantity} for d in o.asks],
        }

    def market_orderbook_get(self, figi, depth):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            return client.market_data.get_order_book(figi=figi, depth=depth)

    def bond_to_json(self, bond):
        return {
            "figi": bond.figi,
            "ticker": bond.ticker,
            "isin": bond.isin,
            "currency": bond.currency,
            "name": bond.name,
            "uid": bond.uid,
            "api_trade_available_flag": bond.api_trade_available_flag,
            "for_qual_investor_flag": bond.for_qual_investor_flag,
            "min_price_increment": cast_money(bond.min_price_increment),
            "nominal": cast_money(bond.nominal),
            "maturity_date": dateToString(bond.maturity_date), # дата погашения
        }

    def shares_to_json(self, bond):
        return {
            "figi": bond.figi,
            "ticker": bond.ticker,
            "isin": bond.isin,
            "currency": bond.currency,
            "name": bond.name,
            "ticker": bond.ticker,
            "min_price_increment": cast_money(bond.min_price_increment),
            "nominal": cast_money(bond.nominal),
        }

    def etfs_to_json(self, bond):
        return {
            "figi": bond.figi,
            "ticker": bond.ticker,
            "isin": bond.isin,
            "currency": bond.currency,
            "name": bond.name,
            "ticker": bond.ticker,
            "min_price_increment": cast_money(bond.min_price_increment),
        }

    def futures_to_json(self, bond):
        print(bond)
        return {
            "figi": bond.figi,
            "ticker": bond.ticker,
            "currency": bond.currency,
            "name": bond.name,
            "ticker": bond.ticker,
            "min_price_increment": cast_money(bond.min_price_increment),
        }    

    def currencies_to_json(self, bond):
        return {
            "figi": bond.figi,
            "ticker": bond.ticker,
            "currency": bond.currency,
            "name": bond.name,
            "ticker": bond.ticker,
            "min_price_increment": cast_money(bond.min_price_increment),
        }


    def market_etfs_get(self):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            return [self.etfs_to_json(d) for d in client.instruments.etfs().instruments]

    def market_currencies_get(self):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            return [self.currencies_to_json(d) for d in client.instruments.currencies().instruments]

    def market_futures_get(self):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            return [self.futures_to_json(d) for d in client.instruments.futures().instruments]

    def market_bonds_get(self):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            return [self.bond_to_json(d) for d in client.instruments.bonds().instruments]

    def market_shares_get(self):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            return [self.shares_to_json(d) for d in client.instruments.shares().instruments]

    def market_bond_info(self, figi):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            for d in client.instruments.bonds().instruments:
                if d.figi==figi:
                    return d    

    def market_bond_info_by_ticker(self, ticker):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            for d in client.instruments.bonds().instruments:
                if d.ticker==ticker:
                    return d

    def market_bond_info_by_isin(self, isin):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            for d in client.instruments.bonds().instruments:
                if d.isin==isin:
                    return d

    def coupon_to_json(self, data):
        return {
            "coupon_date": data.coupon_date,
            "pay_one_bond": cast_money(data.pay_one_bond),
            "coupon_period": data.coupon_period,
        }

    def market_bond_coupons(self, figi):
        start = datetime.now()
        end = datetime.now() + timedelta(days=30*356)
        with Client(self.token, target=INVEST_GRPC_API) as client:
            return [self.coupon_to_json(d) for d in client.instruments.get_bond_coupons(figi=figi, from_ = start, to = end).events]




class InstrumentApi(object):
    def __init__(self, token, account):
        self.account = account
        self.token = token

    def bonds(self):
        with Client(self.token, target=INVEST_GRPC_API) as client:
            return client.instruments.bonds().instruments




class Bondana(object):
    _token = ''
    _account = None

    def __init__(self, token):
        self._token = token        
        with Client(token, target=INVEST_GRPC_API) as client:
            accounts = client.users.get_accounts()
            for acc in accounts.accounts:
                if acc.type==1:
                    print(acc)
                    self.account = acc

        self.orders = OrdersApi(token, account=self.account)
        self.operations = OperationsApi(token, account=self.account)
        self.portfolio = PortfolioApi(token, account=self.account)
        self.market = MarketApi(token, account=self.account)
        self.instruments = InstrumentApi(token, account=self.account)

    def comission(self):
        return 0.5

    def get_balance(self, currency='rub'):
        balance= 0
        blocked = 0
        currencies = self.portfolio.portfolio_currencies_get()
        for m in currencies.money:
            if m.currency == currency:
                balance = cast_money(m)
        for m in currencies.blocked:
            if m.currency==currency:
                blocked = cast_money(m)
        return (balance, blocked)


    def get_all_balances(self):
        currency='rub'
        with Client(self._token, target=INVEST_GRPC_API) as client:
            accounts = client.users.get_accounts()
            for acc in accounts.accounts:
                balance = 0
                blocked = 0
                currencies = client.operations.get_withdraw_limits(account_id=acc.id)
                for m in currencies.money:
                    if m.currency == currency:
                        balance = cast_money(m)
                for m in currencies.blocked:
                    if m.currency==currency:
                        blocked = cast_money(m)
                print(acc.name , balance, blocked)


    def convert_price_from_percent(self, price, nominal):
        return round(price*nominal/100., 7)

    def accounts(self):
        with Client(self._token, target=INVEST_GRPC_API) as client:
            return client.users.get_accounts()

