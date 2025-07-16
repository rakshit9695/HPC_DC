#!/usr/bin/env python3
"""
Blackspring Ridge Wind Farm – HPC Max Power Output Only
=======================================================

This script simulates 24h wind farm output at 5-minute resolution and
outputs only the maximum HPC allocation (30% of AC power) to CSV.

Author: Updated Script
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math

# Wind farm configuration (only Blackspring Ridge)
WIND_FARM = {
    "name": "Blackspring Ridge",
    "lat": 50.4,
    "lon": -112.9,
    "tz": "America/Edmonton",
    "capacity": 300,        # MW
    "num_turbines": 166,
    "turbine": {
        "hub_height": 80,
        "rotor_diameter": 100,
        "rated_power": 1.8,  # MW per turbine
        "cut_in": 3.0,
        "rated": 12.0,
        "cut_out": 25.0
    }
}

# System efficiencies
INVERTER_EFFICIENCY = 0.98
RECTIFIER_EFFICIENCY = 0.97

# Fraction of farm output allocated to HPC (maximum allocation)
HPC_ALLOCATION_MAX = 0.30  # 30%

def wind_power_curve(wind_speed, params):
    if wind_speed < params["cut_in"]:
        return 0
    if wind_speed < params["rated"]:
        ratio = (wind_speed - params["cut_in"]) / (params["rated"] - params["cut_in"])
        return params["rated_power"] * ratio
    if wind_speed <= params["cut_out"]:
        return params["rated_power"]
    return 0

def generate_wind_data(base_date, intervals=288):
    times, speeds = [], []
    for i in range(intervals):
        minutes = i * 5
        t = base_date + timedelta(minutes=minutes)
        hour = minutes / 60.0
        base = 8.0
        diurnal = 3.0 * math.sin(math.pi * (hour - 6) / 12)
        turb = np.random.normal(0, 1.5)
        ws = max(0, base + diurnal + turb)
        times.append(t)
        speeds.append(ws)
    return times, speeds

def calc_power(ws, farm):
    p_turbine = wind_power_curve(ws, farm["turbine"])
    total = p_turbine * farm["num_turbines"]
    # realistic CF scaling from 50% theoretical to 35% actual
    total *= (0.35 / 0.5)
    return min(total, farm["capacity"])

def main():
    date_sim = datetime(2025, 7, 11)
    times, speeds = generate_wind_data(date_sim)

    farm = WIND_FARM

    # Only store Timestamp and HPC_Max_MW
    output_rows = []
    for idx, ws in enumerate(speeds):
        ac = calc_power(ws, farm)
        hpc_max = ac * HPC_ALLOCATION_MAX
        output_rows.append({
            "Timestamp": times[idx],
            "HPC_Max_MW": hpc_max
        })

    # Save CSV with only Timestamp and HPC_Max_MW
    df_out = pd.DataFrame(output_rows)
    filename = "wind_farm_hpc_max_output.csv"
    df_out.to_csv(filename, index=False)

    # Optional: Print summary
    dt_hr = 5/60
    total_hpc_max = df_out["HPC_Max_MW"].sum() * dt_hr
    print(f"\nSimulation Date: {date_sim.date()}")
    print(f"Total HPC Max Allocation: {total_hpc_max:.1f} MWh")
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    main()
