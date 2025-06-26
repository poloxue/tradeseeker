from cli.apis.constant import TRADEAPI_HOST
from cli.apis.auth import AuthAPI


class SpreadTradingAPI:
    """"""

    def __init__(self, auth_api: AuthAPI):
        self.auth_api = auth_api

    def endpoint(self, path):
        return f"{TRADEAPI_HOST}/spreadtrading/{path}"

    def get_all_spread_names(self):
        return self.auth_api.get(self.endpoint("spread_names"))

    def get_all_spreads(self):
        return self.auth_api.get(self.endpoint("spreads"))

    def get_spread(self, name: str):
        return self.auth_api.get(self.endpoint(f"spread/{name}"))

    def get_all_spread_datas(self):
        return self.auth_api.get(self.endpoint("spread_datas"))

    def get_spread_data(self, name: str):
        return self.auth_api.get(self.endpoint(f"spread_data/{name}"))

    def add_spread(self, name, leg_settings, price_formula, active_symbol, min_volume):
        self.auth_api.post(
            self.endpoint("spread/add"),
            data={
                "name": name,
                "leg_settings": leg_settings,
                "price_formula": price_formula,
                "active_symbol": active_symbol,
                "min_volume": min_volume,
            },
        )

    def remove_spread(self, name: str) -> None:
        self.auth_api.post(self.endpoint(f"spread/{name}/remove"))

    def get_strategy_class_names(self):
        return self.auth_api.get(self.endpoint("strategy/class_names"))

    def get_strategy_class_parameters(self, class_name: str):
        return self.auth_api.get(
            self.endpoint(f"strategy/class/{class_name}/parameters")
        )

    def get_all_strategies(self):
        return self.auth_api.get(self.endpoint("strategies"))

    def get_strategy(self, strategy_name: str):
        return self.auth_api.get(self.endpoint(f"strategy/{strategy_name}"))

    def add_strategy(self, class_name, strategy_name, spread_name, setting):
        self.auth_api.post(
            self.endpoint("strategy/add"),
            data={
                "class_name": class_name,
                "strategy_name": strategy_name,
                "spread_name": spread_name,
                "setting": setting,
            },
        )

    def edit_strategy(self, strategy_name, setting):
        self.auth_api.post(
            self.endpoint("strategy/edit"),
            data={
                "strategy_name": strategy_name,
                "setting": setting,
            },
        )

    def init_strategy(self, strategy_name: str):
        self.auth_api.post(self.endpoint(f"strategy/{strategy_name}/init"))

    def start_strategy(self, strategy_name: str):
        self.auth_api.post(self.endpoint(f"strategy/{strategy_name}/start"))

    def stop_strategy(self, strategy_name: str):
        self.auth_api.post(self.endpoint(f"strategy/{strategy_name}/stop"))

    def remove_strategy(self, strategy_name: str):
        self.auth_api.post(self.endpoint(f"strategy/{strategy_name}/remove"))

    def get_all_strategy_algos(self, strategy_name: str):
        self.auth_api.post(self.endpoint(f"strategy/{strategy_name}/algos"))

    def get_all_algos(self):
        self.auth_api.post(self.endpoint("algos"))
