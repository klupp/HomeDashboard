from pandas import DataFrame, read_json


class UtilityData:
    def __init__(self, contracts_df: DataFrame = None, measurements_df: DataFrame = None):
        self.contracts_df = contracts_df
        self.measurements_df = measurements_df

    def refresh(self):
        pass

    def to_json(self, date_format="iso", orient="split"):
        contracts = self.contracts_df.to_json(date_format=date_format, orient=orient)
        measurements = self.measurements_df.to_json(date_format=date_format, orient=orient)
        return "{" + f"\"contracts_df\": {contracts}, \"measurements_df\": {measurements}" + "}"

    @staticmethod
    def from_json(json_data, orient='split'):
        contracts, measurements = json_data.split(", \"measurements_df\": ")
        contracts = contracts[17:]
        measurements = measurements[:-1]
        contracts_df = read_json(contracts, orient=orient)
        measurements_df = read_json(measurements, orient=orient)
        return UtilityData(contracts_df, measurements_df)

