import time
import json
import click
from seeker.apis.auth import AuthAPI
from seeker.apis.spread_trading import SpreadTradingAPI


class SpreadTradingController:
    """"""

    def __init__(
        self,
        vt_symbol_1,
        vt_symbol_2,
        leg_settings,
        active_symbol,
        price_formula,
        min_volume,
        strategy_class_name,
        strategy_setting,
        auth_api,
    ):
        self.strategy_class_name = strategy_class_name
        self.vt_symbol_1 = vt_symbol_1
        self.vt_symbol_2 = vt_symbol_2
        self.leg_settings = leg_settings
        self.active_symbol = active_symbol
        self.price_formula = price_formula
        self.min_volume = min_volume

        self.spread_name = f"{vt_symbol_1}-{vt_symbol_2}"
        self.strategy_name = f"{self.strategy_class_name}-{self.spread_name}"
        self.strategy_setting = strategy_setting

        self.spread_trading_api = SpreadTradingAPI(auth_api)

    def add_spread(self):
        price_formula = "A/B*1000"
        self.spread_trading_api.add_spread(
            name=self.spread_name,
            leg_settings=self.leg_settings,
            active_symbol=self.active_symbol,
            price_formula=price_formula,
            min_volume=self.min_volume,
        )

    def add_strategy(self):
        self.spread_trading_api.add_strategy(
            self.strategy_class_name,
            strategy_name=self.strategy_name,
            spread_name=self.spread_name,
            setting=self.strategy_setting,
        )

    def start_strategy(self):
        self.spread_trading_api.init_strategy(self.strategy_name)
        while True:
            time.sleep(1)
            strategy = self.spread_trading_api.get_strategy(self.strategy_name)
            if strategy["variables"]["inited"]:
                break

        self.spread_trading_api.start_strategy(self.strategy_name)

    def stop(self):
        self.spread_trading_api.stop_strategy(self.strategy_name)


@click.group()
def cli():
    pass


@cli.command("basic-spread")
@click.option("--conf", "config_path", help="Config file path")
@click.option("--max-pos", required=True, type=click.INT, help="Parameter max pos")
def basic_spread(config_path, max_pos):
    config = json.load(open(config_path))

    security = json.load(open("security.json"))
    auth_api = AuthAPI()
    auth_api.login(**security)

    vt_symbol_1 = config["vt_symbol_1"]
    vt_symbol_2 = config["vt_symbol_2"]
    leg_settings = config["leg_settings"]
    active_symbol = config["active_symbol"]
    price_formula = config["price_formula"]
    min_volume = config["min_volume"]

    strategy_class_name = "BasicSpreadStrategy"
    strategy_setting = {
        "buy_price": 995,
        "sell_price": 999,
        "short_price": 1005,
        "cover_price": 1001,
        "interval": 5,
        "max_pos": max_pos,
    }

    ctrl = SpreadTradingController(
        vt_symbol_1=vt_symbol_1,
        vt_symbol_2=vt_symbol_2,
        leg_settings=leg_settings,
        active_symbol=active_symbol,
        price_formula=price_formula,
        min_volume=min_volume,
        strategy_class_name=strategy_class_name,
        strategy_setting=strategy_setting,
        auth_api=auth_api,
    )

    input("Press any key to continue -> add_spread")
    ctrl.add_spread()
    input("Press any key to continue -> add_strategy")
    ctrl.add_strategy()
    input("Press any key to continue -> start_strategy")
    ctrl.start_strategy()


def main():
    cli()


if __name__ == "__main__":
    main()
