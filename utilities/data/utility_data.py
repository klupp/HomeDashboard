from pandas import DataFrame


class UtilityData:
    def __init__(self, contracts_df: DataFrame = None, measurements_df: DataFrame = None):
        self.contracts_df = contracts_df
        self.measurements_df = measurements_df

    def refresh(self):
        pass
