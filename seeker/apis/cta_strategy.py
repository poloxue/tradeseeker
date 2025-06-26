from cli.apis.auth import AuthAPI, TRADEAPI_HOST


class CtaStrategyAPI:
    """"""

    def __init__(self, auth_api: AuthAPI):
        self.auth_api = auth_api

    def endpoint(self, path):
        return f"{TRADEAPI_HOST}/cta/{path}"

    def strategy_templates(self):
        self.auth_api.request(
            method="get",
            url=self.endpoint("strategy_class_names"),
        )

    def strategy_class_parameters(self, class_name):
        self.auth_api.request(
            method="get",
            url=self.endpoint(f"strategy_class_parameters/{class_name}"),
        )

    def all_strategies(self):
        self.auth_api.request(method="get", url=self.endpoint("strategies"))

    def get_strategy(self, strategy_name):
        self.auth_api.request(
            method="get", url=self.endpoint(f"strategy/{strategy_name}")
        )

    def add_strategy(self, class_name, strategy_name, vt_symbol, setting):
        self.auth_api.request(
            method="post",
            url=self.endpoint("add_strategy"),
            data={
                "class_name": class_name,
                "strategy_name": strategy_name,
                "vt_symbol": vt_symbol,
                "setting": dict(setting),
            },
        )

    def init_strategy(self, strategy_name):
        self.auth_api.request(
            method="post",
            url=self.endpoint(f"init_strategy/{strategy_name}"),
        )

    def start_strategy(self, strategy_name):
        self.auth_api.request(
            method="post",
            url=self.endpoint(f"start_strategy/{strategy_name}"),
        )

    def stop_strategy(self, strategy_name):
        self.auth_api.request(
            method="post", url=self.endpoint(f"stop_strategy/{strategy_name}")
        )

    def remove_strategy(self, strategy_name):
        self.auth_api.request(
            method="post",
            url=self.endpoint(f"remove_strategy/{strategy_name}"),
        )
