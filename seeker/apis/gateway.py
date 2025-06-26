from cli.api import request, endpoint


class GatwayService:
    def all_contracts(self, product):
        contracts = request(method="get", url=endpoint("contract"))
        for contract in contracts:
            if product and contract["product"] != product:
                continue
            print(contract["vt_symbol"], contract["name"], contract["product"])
