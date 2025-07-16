#!/usr/bin/env python3
"""
HPC Data Center Load Profile Generator
======================================

This script prompts for an HPC data center size (1–10 MW), then generates
a 24-hour load profile at 5-minute resolution, and saves it to CSV.

Author: HPC Configuration Generator
Based on industry research and Canadian standards
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import math

# ---------------------------------------------------------------------------
# 1.  INITIALIZATIONS (unchanged)
# ---------------------------------------------------------------------------
# Rack power density (kW)
RACK_POWER_KW = 12
# Node counts per rack by DC size tier
NODE_DENSITY = {
    'small': 24,   # ≤2 MW
    'medium': 36,  # >2–5 MW
    'large': 48    # >5 MW
}
# Node type ratios
GPU_RATIO = 0.4
CPU_RATIO = 0.5
ASIC_RATIO = 0.1
# Node power consumption (W)
GPU_POWER_W = 4 * 700   # 4 GPUs × 700 W
CPU_POWER_W = 2 * 300   # 2 CPUs × 300 W
ASIC_POWER_W = 400
# Ancillary per-node (W)
STORAGE_W = 50
NETWORK_W = 30
# PUE and utilization
DESIGN_PUE = 1.3
UTILIZATION = 0.75
# Time resolution
INTERVAL_MIN = 5
INTERVAL_HR = INTERVAL_MIN / 60.0

# ---------------------------------------------------------------------------
# 2.  USER INPUT FUNCTION
# ---------------------------------------------------------------------------
def prompt_dc_size():
    """Prompt user for DC size in MW (1–10)."""
    while True:
        try:
            size = float(input("Enter data center size in MW (1–10): "))
            if 1 <= size <= 10:
                return size
            print("Please enter a value between 1 and 10")
        except ValueError:
            print("Invalid entry; please enter a number")

# ---------------------------------------------------------------------------
# 3.  COMPUTE LOAD PROFILE
# ---------------------------------------------------------------------------
def build_load_profile(dc_size_mw):
    """
    Generate a 24h load profile at 5-minute steps for given DC size.
    Returns a DataFrame with timestamp and total load (kW).
    """
    # Compute racks and nodes
    num_racks = int((dc_size_mw * 1000) / RACK_POWER_KW)
    if dc_size_mw <= 2:
        nodes_per_rack = NODE_DENSITY['small']
    elif dc_size_mw <= 5:
        nodes_per_rack = NODE_DENSITY['medium']
    else:
        nodes_per_rack = NODE_DENSITY['large']
    total_nodes = num_racks * nodes_per_rack

    # Per-node peak load (W)
    peak_node_w = (
        GPU_RATIO * GPU_POWER_W +
        CPU_RATIO * CPU_POWER_W +
        ASIC_RATIO * ASIC_POWER_W +
        STORAGE_W +
        NETWORK_W
    )
    # Convert to kW and apply utilization & PUE
    peak_node_kw = peak_node_w / 1000.0
    effective_peak_kw = peak_node_kw * UTILIZATION * DESIGN_PUE

    # Build timestamps
    start = datetime.combine(datetime.today(), datetime.min.time())
    timestamps = [start + timedelta(minutes=i * INTERVAL_MIN) for i in range(int(24*60/INTERVAL_MIN))]

    # Generate diurnal shape (e.g., higher daytime load, lower at night)
    hours = np.array([t.hour + t.minute/60 for t in timestamps])
    diurnal_factor = 0.6 + 0.4 * np.sin((hours - 6) * np.pi / 12)  # varies 0.2–1.0
    diurnal_factor = np.clip(diurnal_factor, 0.2, 1.0)

    # Compute load
    per_node_load_kw = effective_peak_kw * diurnal_factor
    total_load_kw = per_node_load_kw * total_nodes

    # Assemble DataFrame
    df = pd.DataFrame({
        'Timestamp': timestamps,
        'Load_kW': total_load_kw.round(2)
    })
    return df

# ---------------------------------------------------------------------------
# 4.  MAIN
# ---------------------------------------------------------------------------
def main():
    print("HPC Data Center Load Profile Generator\n")
    dc_size = prompt_dc_size()
    print(f"\nGenerating 24h load profile for {dc_size:.1f} MW DC...")
    profile_df = build_load_profile(dc_size)
    filename = f"dc_{int(dc_size)}MW_load_profile.csv"
    profile_df.to_csv(filename, index=False)
    print(f"Load profile saved to {filename}")

if __name__ == "__main__":
    main()
