import os
import pandas as pd
import numpy as np

from utilities.data.utility_data import UtilityData

utilities_repo_url = 'git@github.com:klupp/HomeExpenses.git'
utilities_dir = '../Utilities/'


def refresh():
    utilities_exist = os.path.exists(utilities_dir)
    if utilities_exist:
        cwd = os.getcwd()
        os.chdir(utilities_dir)
        os.system('git pull')
        os.chdir(cwd)
    else:

        os.system(f'git clone {utilities_repo_url} {utilities_dir}')


def is_available(refresh_data=True) -> bool:
    if refresh_data:
        refresh()
    return os.path.exists(utilities_dir)


def fetch(refresh_data=True) -> UtilityData:
    if refresh_data:
        refresh()
    contracts_df = pd.read_csv(utilities_dir + "Contracts.csv")
    measurements_df = pd.read_csv(utilities_dir + 'measurements.csv')
    measurements_df['date'] = pd.to_datetime(measurements_df['date'])
    measurements_df = prepare_data(contracts_df, measurements_df)
    measurements_df.sort_values(by='date', inplace=True)
    return UtilityData(contracts_df, measurements_df)


def prepare_data(contract_df, measure_df):
    df = measure_df
    # Transform all measure units to kWh
    df.loc[df['measure_unit'] == 'mWh', 'aggregate_consumption'] *= 1000
    df.loc[df['measure_unit'] == 'mWh', 'measure_unit'] = 'kWh'

    df.loc[df['measure_unit'] == 'm3', 'aggregate_consumption'] *= 10.6
    df.loc[df['measure_unit'] == 'm3', 'measure_unit'] = 'kWh'

    # Join with contracts to expand information for each measurement.
    df = df.merge(contract_df, left_on='contract', right_on='ID', sort=False)

    # Order by date. IMPORTANT!!!
    df.sort_values(by='date', inplace=True, ignore_index=True)

    # Handle meter changes (restart of the counter). For each address and type of meters.
    df["TypeAddress"] = df['Type'] + " - " + df['Address']

    for meter in df["TypeAddress"].unique():
        zeros = df.index[(df['TypeAddress'] == meter) & (df['aggregate_consumption'] == 0)]
        for zero in np.flip(zeros):
            zeros_mask = np.zeros(df.shape[0])
            zeros_mask[zero:] = 1
            df.loc[(df['TypeAddress'] == meter) & zeros_mask, 'aggregate_consumption'] += df['aggregate_consumption'][
                zero - 1]

    min_contract_year = df['ContractYear'].min()

    for contract_name in df['ContractName'].unique():
        year = contract_df[contract_df['ContractName'] == contract_name]['ContractYear'].min()
        df.loc[df['ContractName'] == contract_name, 'date'] -= pd.offsets.DateOffset(
            years=(year - min_contract_year))
        df.loc[df['ContractName'] == contract_name, 'aggregate_consumption'] -= \
            df[df['ContractName'] == contract_name]['aggregate_consumption'].min()

    return df



