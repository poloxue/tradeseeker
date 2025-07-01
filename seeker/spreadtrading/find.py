import os
import json
import click
import asyncio
import itertools
from tqdm import tqdm

from collections import defaultdict

import ccxt.pro

from tabulate import tabulate

from seeker.utils import send_lark


def load_ignore_spreads():
    spreads = json.load(open("ignore_spreads.json", "r+"))
    if not spreads:
        return []
    else:
        return spreads


params = {
    "enableRateLimit": True,
    "proxies": {
        "http": os.getenv("http_proxy"),
        "https": os.getenv("http_proxy"),
    },
    "aiohttp_proxy": os.getenv("http_proxy"),
}


def create_exchange(name):
    if not hasattr(ccxt.pro, name):
        raise ValueError(f"No exchange named {name}")

    return getattr(ccxt.pro, name)(params)


def calculate_order_contracts(a_market, b_market, a_price, b_price):
    a_contract_size = a_market["contractSize"]  # 合约乘数
    b_contract_size = b_market["contractSize"]

    a_min_contracts = a_market["limits"]["amount"]["min"]  # 合约的最小数量
    b_min_contracts = b_market["limits"]["amount"]["min"]
    a_min_value = a_min_contracts * a_contract_size  # 一笔交易的最小价值
    b_min_value = b_min_contracts * b_contract_size

    a_min_cost = a_market["limits"]["cost"]["min"]
    b_min_cost = b_market["limits"]["cost"]["min"]

    a_min_cost = 0 if a_min_cost is None else a_min_cost
    b_min_cost = 0 if b_min_cost is None else b_min_cost

    a_min_value = max(a_min_value, a_min_cost / a_price + a_min_value)
    b_min_value = max(b_min_value, b_min_cost / b_price + b_min_value)

    if a_min_value < b_min_value:
        return (
            a_min_value / a_contract_size * b_min_value / a_min_value,
            b_min_value / b_contract_size,
        )
    else:
        return (
            a_min_value / a_contract_size,
            b_min_value / b_contract_size * a_min_value / b_min_value,
        )


stable_ccys = ["USDT", "BUSD", "USDC", "FDUSD", "DAI", "USDE", "USD"]


async def seek(exchange_names, min_spread, ignore_spreads):
    exchanges = []
    for exchange_name in exchange_names:
        exchanges.append(create_exchange(exchange_name))

    base_id_markets_map = defaultdict(list)
    for exchange in exchanges:
        markets = await exchange.load_markets()
        for m in markets.values():
            quote_id = m["quoteId"]
            base_id = m["baseId"]
            if m["swap"] and m["active"] and base_id and quote_id in stable_ccys:
                m["exchange"] = exchange
                base_id_markets_map[m["baseId"]].append(m)

    for base_id, markets in base_id_markets_map.items():
        if not markets:
            del base_id_markets_map[base_id]

    results = []
    for markets in tqdm(base_id_markets_map.values()):
        spread_markets = itertools.combinations(markets, 2)
        for a_market, b_market in spread_markets:
            a_exchange = a_market["exchange"]
            b_exchange = b_market["exchange"]
            a_name = a_exchange.name
            b_name = b_exchange.name

            a_symbol = a_market["symbol"]
            b_symbol = b_market["symbol"]

            a_vt_symbol = f"{a_market['baseId']}{a_market['quoteId']}_SWAP_{a_name.upper()}.GLOBAL"
            b_vt_symbol = f"{b_market['baseId']}{b_market['quoteId']}_SWAP_{b_name.upper()}.GLOBAL"

            spread_name = f"{a_vt_symbol}-{b_vt_symbol}"
            if spread_name in ignore_spreads:
                continue

            try:
                a_funding, b_funding, a_orderbook, b_orderbook = await asyncio.gather(
                    a_exchange.fetch_funding_rate(a_symbol),
                    b_exchange.fetch_funding_rate(b_symbol),
                    a_exchange.fetch_order_book(a_symbol),
                    b_exchange.fetch_order_book(b_symbol),
                )
            except Exception as e:
                print(f"Exception {e}")
                continue

            a_bid = a_orderbook["bids"][0][0]
            a_ask = a_orderbook["asks"][0][0]
            b_bid = b_orderbook["bids"][0][0]
            b_ask = b_orderbook["asks"][0][0]

            a_funding_rate = a_funding["fundingRate"]
            b_funding_rate = b_funding["fundingRate"]

            funding_rate_spread = a_funding_rate - b_funding_rate

            long_spread = (b_bid - a_ask) / a_ask - funding_rate_spread
            short_spread = (a_bid - b_ask) / b_ask + funding_rate_spread

            if long_spread > min_spread:
                a_contracts, b_contracts = calculate_order_contracts(
                    a_market, b_market, a_ask, b_bid
                )
            elif short_spread > min_spread:
                a_contracts, b_contracts = calculate_order_contracts(
                    a_market, b_market, a_bid, b_ask
                )
            else:
                continue

            if a_contracts < b_contracts:
                multiplier = int(b_contracts / (b_contracts / a_contracts) + 1)
                a_trading_multiplier = multiplier
                b_trading_multiplier = -b_contracts / a_contracts * multiplier
                min_volume = 1
            elif a_contracts > b_contracts:
                multiplier = int(a_contracts / (a_contracts / b_contracts) + 1)
                a_trading_multiplier = a_contracts / b_contracts * multiplier
                b_trading_multiplier = -multiplier
                min_volume = 1
            else:
                continue

            a_trading_direction = 1
            b_trading_direction = -1

            result = {
                "vt_symbol_1": a_vt_symbol,
                "vt_symbol_2": b_vt_symbol,
                "leg_settings": [
                    {
                        "vt_symbol": a_vt_symbol,
                        "variable": "A",
                        "trading_direction": a_trading_direction,
                        "trading_multiplier": a_trading_multiplier,
                    },
                    {
                        "vt_symbol": b_vt_symbol,
                        "variable": "B",
                        "trading_direction": b_trading_direction,
                        "trading_multiplier": b_trading_multiplier,
                    },
                ],
                "price_formula": "A/B*1000",
                "active_symbol": a_vt_symbol,
                "min_volume": min_volume,
                "extras": {
                    "spread": f"{max(long_spread, short_spread):.5f}",
                    "long_spread": f"{long_spread:.5f}",
                    "short_spread": f"{short_spread:.5f}",
                    "funding_rate_spread": f"{funding_rate_spread:.5f}",
                },
            }
            json.dump(result, indent=True, fp=open(f"{spread_name}.json", "w"))
            results.append(result)

            send_lark(f"价差机会-{spread_name}", body=json.dumps(result, indent=True))

    print(tabulate(results, headers="keys", tablefmt="pretty"))

    for exchange in exchanges:
        await exchange.close()


@click.group()
def cli():
    pass


@click.command()
@click.option("--exchange-names", default="okx,binance", help="交易所名称列表")
@click.option(
    "--min-spread",
    default=0.002,
    help="最小价差阈值(例如. 0.002)",
)
def main(exchange_names, min_spread):
    ignore_spreads = load_ignore_spreads()
    exchange_names = exchange_names.split(",")
    asyncio.run(seek(exchange_names, min_spread, ignore_spreads))


if __name__ == "__main__":
    main()
