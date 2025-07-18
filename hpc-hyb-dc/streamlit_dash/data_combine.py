import streamlit as st
import pandas as pd
import numpy as np

WIND_FILE = "/Users/sarthak/Desktop/LHE Digitial Twin/Final_Implementation/hpc-hyb-dc/src/hpp_core/csv_files/wind_farm_hpc_max_output.csv"
SOLAR_FILE = "/Users/sarthak/Desktop/LHE Digitial Twin/Final_Implementation/hpc-hyb-dc/src/hpp_core/csv_files/solar_out.csv"

def wind_load_combi(load_df, farm_ratio, windfarms):
    # Load CSVs
    load_df = load_df.copy()
    load_df["Load_MW"] = load_df["Load_kW"]*0.001
    wind_df = pd.read_csv(WIND_FILE)
    wind_df["Timestamp"] = pd.to_datetime(wind_df["Timestamp"])
    wind_df = wind_df.copy()

    load_df["Time"] = load_df["Timestamp"].dt.time
    wind_df["Time"] = wind_df["Timestamp"].dt.time

    # Merge on 'Time' instead of full Timestamp
    merged_df = pd.merge(load_df, wind_df, on="Time", suffixes=('_load', '_wind'))

    # Calculate wind output
    merged_df["wind_output"] = merged_df.apply(
        lambda row: min(row["HPC_Max_MW"]*windfarms, row["Load_MW"]*farm_ratio), axis=1
    )

    # print(merged_df)
    return merged_df

def solar_load_combi(wind_load_df, farm_ratio, solarfarms):
    wind_load_df = wind_load_df.copy()

    solar_df = pd.read_csv(SOLAR_FILE)
    solar_df["Timestamp"] = pd.to_datetime(solar_df["Timestamp"])
    solar_df = solar_df.copy()

    solar_df["AC_MW"] = solar_df["AC_kW"]*0.001
    solar_df["Time"] = solar_df["Timestamp"].dt.time

    solar_combi_df = pd.merge(wind_load_df, solar_df, on="Time", suffixes=('_load', '_solar'))
    solar_combi_df["solar_output"] = solar_combi_df.apply(
        lambda row: min(row["AC_MW"]*solarfarms, row["Load_MW"]*(1-farm_ratio)), axis=1
    )
    # print(solar_combi_df)
    return solar_combi_df

def energy_sum_profile(solar_combi_df):
    
    solar_combi_df = solar_combi_df.copy()

    solar_combi_df["net_output"] = solar_combi_df.apply(
        lambda row: row["solar_output"]+ row["wind_output"], axis=1
    ) 
    # print (solar_combi_df)
    return solar_combi_df
    
