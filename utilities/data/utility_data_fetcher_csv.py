import numpy as np
import pandas as pd
from pandas import DataFrame

from utilities import UtilityData


class UtilityDataFetcherCSV(UtilityData):
    def __init__(
            self,
            measurements_source='https://raw.githubusercontent.com/klupp/HomeExpenses/main/measurements.csv',
            contracts_source='https://raw.githubusercontent.com/klupp/HomeExpenses/main/contracts/contract.csv',
            contract_anex_source='https://raw.githubusercontent.com/klupp/HomeExpenses/main/contracts/contract_anex.csv',
            contract_payment_plan_source='https://raw.githubusercontent.com/klupp/HomeExpenses/main/contracts/contract_payment_plan.csv',
            contract_settlement_source='https://raw.githubusercontent.com/klupp/HomeExpenses/main/contracts/contract_settlement.csv',
            contract_bonus_source='https://raw.githubusercontent.com/klupp/HomeExpenses/main/contracts/contract_bonus.csv'

    ):
        super().__init__()
        self.utilities_measurements_source = measurements_source
        self.utilities_contracts_source = contracts_source
        self.utilities_contract_anex_source = contract_anex_source
        self.utilities_contract_payment_plan_source = contract_payment_plan_source
        self.utilities_contract_settlement_source = contract_settlement_source
        self.utilities_contract_bonus_source = contract_bonus_source
        self.refresh()

    def refresh(self):
        self.contracts_df = pd.read_csv(self.utilities_contracts_source)
        self.contracts_df['From'] = pd.to_datetime(self.contracts_df['From'])
        self.contracts_df['To'] = pd.to_datetime(self.contracts_df['To'])

        self.contract_anex_df = pd.read_csv(self.utilities_contract_anex_source)
        self.contract_anex_df['AnexStart'] = pd.to_datetime(self.contract_anex_df['AnexStart'])
        self.contract_anex_df['AnexEnd'] = pd.to_datetime(self.contract_anex_df['AnexEnd'])

        self.contract_settlement_df = pd.read_csv(self.utilities_contract_settlement_source)
        self.contract_settlement_df['SettlementDate'] = pd.to_datetime(self.contract_settlement_df['SettlementDate'])

        self.contract_bonus_df = pd.read_csv(self.utilities_contract_bonus_source)
        self.contract_bonus_df['BonusDate'] = pd.to_datetime(self.contract_bonus_df['BonusDate'])

        self.contract_payment_plan_df = pd.read_csv(self.utilities_contract_payment_plan_source)
        self.contract_payment_plan_df['PaymentDate'] = pd.to_datetime(self.contract_payment_plan_df['PaymentDate'])
        self.contract_payment_plan_df = UtilityDataFetcherCSV.prepare_payment_plan(self.contract_payment_plan_df,
                                                                                   self.contract_settlement_df,
                                                                                   self.contracts_df)

        measurements_df = pd.read_csv(self.utilities_measurements_source)
        measurements_df['date'] = pd.to_datetime(measurements_df['date'])
        measurements_df = UtilityDataFetcherCSV.prepare_data(measurements_df, self.contracts_df, self.contract_anex_df)
        measurements_df.sort_values(by='date', inplace=True)
        self.measurements_df = measurements_df

    @staticmethod
    def prepare_payment_plan(payment_plan_df: DataFrame, settlement_df: DataFrame, contract_df: DataFrame):
        df = payment_plan_df.copy()

        df_start_contracts = contract_df[['From', "ID"]]
        df_start_contracts['PaymentAmount'] = 0
        df_start_contracts['PaymentID'] = 'Start'
        df_start_contracts.columns = ['PaymentDate', 'ContractID', 'PaymentAmount', 'PaymentID']

        df_end_contracts = contract_df[['To', "ID"]]
        df_end_contracts['PaymentAmount'] = 0
        df_end_contracts['PaymentID'] = 'End'
        df_end_contracts.columns = ['PaymentDate', 'ContractID', 'PaymentAmount', 'PaymentID']

        settlements = settlement_df[['ContractID', 'SettlementDate', 'SettlementAmount']].copy()
        settlements.columns = ['ContractID', 'PaymentDate', 'PaymentAmount']
        settlements['PaymentID'] = 'Settlement'

        df = pd.concat([df, df_start_contracts, df_end_contracts, settlements], ignore_index=True)
        df.sort_values(by='PaymentDate', inplace=True, ignore_index=True)

        # Calculate aggregate price
        df['AggregatePaymentAmount'] = 0
        for contract in df["ContractID"].unique():
            df.loc[df['ContractID'] == contract, 'AggregatePaymentAmount'] = \
                df[df['ContractID'] == contract]['PaymentAmount'].cumsum()

        # Stack contract periods over each other
        min_contract_year = df['PaymentDate'].dt.year.min()
        for contract_name in df['ContractID'].unique():
            year = df[df['ContractID'] == contract_name]['PaymentDate'].dt.year.min()
            df.loc[df['ContractID'] == contract_name, 'PaymentDate'] -= pd.offsets.DateOffset(
                years=(year - min_contract_year))
        return df

    @staticmethod
    def prepare_data(measure_df: DataFrame, contract_df: DataFrame, contract_anex_df: DataFrame):
        measure_df_columns = measure_df.columns
        df = measure_df.copy()

        # Join with contracts to expand information for each measurement.
        df = df.merge(contract_df, left_on='contract', right_on='ID', sort=False)

        # Order by date. IMPORTANT!!!
        df.sort_values(by='date', inplace=True, ignore_index=True)

        # Transform all measure units to kWh
        df.loc[df['measure_unit'] == 'mWh', 'aggregate_consumption'] *= 1000
        df.loc[df['measure_unit'] == 'mWh', 'measure_unit'] = 'kWh'

        df.loc[df['measure_unit'] == 'm3', 'aggregate_consumption'] *= 10.92
        df.loc[df['measure_unit'] == 'm3', 'measure_unit'] = 'kWh'

        # Handle meter changes (restart of the counter). For each address and type of meters.
        df["TypeAddress"] = df['Type'] + " - " + df['Address']

        for meter in df["TypeAddress"].unique():
            at_df = df[df['TypeAddress'] == meter]
            at_df_index = np.array(at_df.index)
            zeros = at_df.index[at_df['aggregate_consumption'] == 0]
            for zero in np.flip(zeros):
                zero_loc = np.where(at_df_index == zero)[0][0]
                if zero_loc == 0:
                    continue
                for_update_mask = np.zeros(df.shape[0])
                for_update_mask[zero:] = 1
                df.loc[(df['TypeAddress'] == meter) & for_update_mask, 'aggregate_consumption'] += \
                    df.at[at_df_index[zero_loc - 1], 'aggregate_consumption']

        old_contract_df = contract_df[contract_df['To'] < pd.Timestamp.now()]
        df_interpol = df[['date', 'contract', 'aggregate_consumption']].copy()
        df_start_contracts = old_contract_df[['From', "ID"]]
        df_start_contracts['aggregate_consumption'] = np.NAN
        df_start_contracts.columns = ['date', 'contract', 'aggregate_consumption']

        df_end_contracts = old_contract_df[['To', "ID"]]
        df_end_contracts['aggregate_consumption'] = np.NAN
        df_end_contracts.columns = ['date', 'contract', 'aggregate_consumption']

        df_interpol = pd.concat([df_interpol, df_start_contracts, df_end_contracts], ignore_index=True)
        df_interpol.sort_values(by='date', inplace=True, ignore_index=True)
        df_interpol.index = df_interpol['date']
        del df_interpol['date']
        df_interpol = df_interpol.groupby('contract') \
            .resample('D') \
            .mean()
        df_interpol['aggregate_consumption'] = df_interpol['aggregate_consumption'].interpolate(limit_direction='both')
        df_interpol = df_interpol.reset_index()

        df = df_interpol

        # Join with contracts to expand information for each measurement.
        df = df.merge(contract_df, left_on='contract', right_on='ID', sort=False)

        # Order by date. IMPORTANT!!!
        df.sort_values(by='date', inplace=True, ignore_index=True)

        df = df[(df['date'] >= df['From']) & (df['date'] <= df['To'])]

        # Start every contract from 0 kWh
        for contract_name in df['contract'].unique():
            contract_mask = df['contract'] == contract_name
            df.loc[contract_mask, 'aggregate_consumption'] -= \
                df[contract_mask]['aggregate_consumption'].min()

        # Calculate consumption
        df['consumption'] = 0
        for contract in df["contract"].unique():
            meter_df = df[df['contract'] == contract].copy()
            aggregate_consumption = meter_df.aggregate_consumption.to_numpy()
            aggregate_consumption_shifted = np.concatenate(([aggregate_consumption[0]], aggregate_consumption))[0:-1]
            df.loc[df['contract'] == contract, 'consumption'] = (
                    aggregate_consumption - aggregate_consumption_shifted).clip(min=0)

        # Calculate price
        # to calculate the price first we have to join with the contract anexes
        df = df.merge(contract_anex_df, left_on='contract', right_on='ContractID', sort=False)
        df = df[(df['date'] >= df['AnexStart']) & (df['date'] <= df['AnexEnd'])]

        df['price'] = (df['consumption'] * df['Price/Unit'] + df['YearlyBasePrice'] / 365) * (
                    1 + df['VAT%'] * 1.0 / 100)

        # Order by date. IMPORTANT!!!
        df.sort_values(by='date', inplace=True, ignore_index=True)

        # Calculate aggregate price
        df['aggregate_price'] = 0
        for contract in df["contract"].unique():
            df.loc[df['contract'] == contract, 'aggregate_price'] = df[df['contract'] == contract]['price'].cumsum()

        # Stack contract periods over each other
        min_contract_year = df['ContractYear'].min()
        for contract_name in df['ContractName'].unique():
            year = contract_df[contract_df['ContractName'] == contract_name]['ContractYear'].min()
            df.loc[df['ContractName'] == contract_name, 'date'] -= pd.offsets.DateOffset(
                years=(year - min_contract_year))

        # Continuous consumption
        # for consumption_type in contract_df["Type"].unique():
        #     years = contract_df[contract_df.Type == consumption_type].ContractYear.unique()
        #     years = np.flip(years[1:])
        #     for year in years:
        #         df.loc[(df.Type == consumption_type) & (df.ContractYear >= year), 'aggregate_consumption'] += df[
        #             (df.Type == consumption_type) & (df.ContractYear == (year - 1))]['aggregate_consumption'].max()

        return df[['date', 'contract', 'consumption', 'aggregate_consumption', 'price', 'aggregate_price']].copy()
