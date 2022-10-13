from pandas import DataFrame


class UtilityData:
    def __init__(self, contracts_df: DataFrame, measurements_df: DataFrame):
        self.contracts_df = contracts_df
        self.measurements_df = measurements_df
