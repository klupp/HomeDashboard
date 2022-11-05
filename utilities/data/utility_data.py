from pandas import DataFrame, read_json
import re


class UtilityData:
    def __init__(
            self,
            measurements_df: DataFrame = None,
            contracts_df: DataFrame = None,
            contract_anex_df: DataFrame = None,
            contract_payment_plan_df: DataFrame = None,
            contract_settlement_df: DataFrame = None,
            contract_bonus_df: DataFrame = None
    ):
        self.measurements_df = measurements_df
        self.contracts_df = contracts_df
        self.contract_anex_df = contract_anex_df
        self.contract_payment_plan_df = contract_payment_plan_df
        self.contract_settlement_df = contract_settlement_df
        self.contract_bonus_df = contract_bonus_df

    def refresh(self):
        pass

    def to_json(self, date_format="iso", orient="split"):
        contracts = self.contracts_df.to_json(date_format=date_format, orient=orient)
        contract_anex = self.contract_anex_df.to_json(date_format=date_format, orient=orient)
        contract_payment_plan = self.contract_payment_plan_df.to_json(date_format=date_format, orient=orient)
        contract_settlement = self.contract_settlement_df.to_json(date_format=date_format, orient=orient)
        contract_bonus = self.contract_bonus_df.to_json(date_format=date_format, orient=orient)
        measurements = self.measurements_df.to_json(date_format=date_format, orient=orient)
        json_object = f"""
                {{
                    "measurements_df": {measurements},
                    "contracts_df": {contracts},
                    "contract_anex_df": {contract_anex},
                    "contract_payment_plan_df": {contract_payment_plan},
                    "contract_settlement_df": {contract_settlement},
                    "contract_bonus_df": {contract_bonus}
                }}
            """
        # simplify json by removing any empty lines and spaces.
        json_object = re.sub(r"[\n\t\s]*", "", json_object)
        return json_object

    @staticmethod
    def from_json(json_data, orient='split'):
        json_data = json_data[19:-1]
        measurements, json_data = json_data.split(",\"contracts_df\":")
        contracts, json_data = json_data.split(",\"contract_anex_df\":")
        contract_anex, json_data = json_data.split(",\"contract_payment_plan_df\":")
        contract_payment_plan, json_data = json_data.split(",\"contract_settlement_df\":")
        contract_settlement, contract_bonus = json_data.split(",\"contract_bonus_df\":")

        measurements_df = read_json(measurements, orient=orient)
        contracts_df = read_json(contracts, orient=orient)
        contract_anex_df = read_json(contract_anex, orient=orient)
        contract_payment_plan_df = read_json(contract_payment_plan, orient=orient)
        contract_settlement_df = read_json(contract_settlement, orient=orient)
        contract_bonus_df = read_json(contract_bonus, orient=orient)
        return UtilityData(
            measurements_df,
            contracts_df,
            contract_anex_df,
            contract_payment_plan_df,
            contract_settlement_df,
            contract_bonus_df
        )

