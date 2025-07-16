#!/usr/bin/env python3
"""
One-Day Solar-PV Simulator (5-min resolution)

• Computes AC & DC power, plane-of-array (POA) irradiance, and module temperature
• Resolution: 5 minutes
• Stores results in solar_out.csv
• Plots time-series of all parameters
"""

from datetime import datetime, timedelta, date
import math
import pathlib
import pandas as pd
import matplotlib.pyplot as plt

# ───────────────────────────────────────────────────────────────────────────────
# 1.  Project configuration (full dictionary)
# ───────────────────────────────────────────────────────────────────────────────
PROJECT_CONFIG = {
    "project_name": "CA_PV_ED Project",
    "location": {
        "city": "Highvale",
        "region": "Alberta",
        "country": "Canada",
        "latitude": 53.49,
        "longitude": -114.49,
        "altitude": 742.26
    },
    "rated_power_ac": 38.9,      # MWac
    "peak_power_dc": 50.6,       # MWdc
    "dc_ac_ratio": 1.30,
    "pv_modules": {
        "peak_power": 625.0,     # W
        "quantity": 80912,
        "efficiency": 23.14
    },
    "inverters": {
        "quantity": 12,
        "rated_power": 3600.0    # kW
    },
    "tilt_angle": 18.0,          # °
    "azimuth_angle": 0.0,        # °
    "monthly_ghi": [28.1, 51.8, 100.0, 136.1, 172.1, 176.2,
                    179.7, 151.8, 102.0, 59.7, 30.7, 21.0],   # kWh/m²
    "monthly_temp": [-8.47, -2.16, -5.69, 2.17, 11.25, 14.75,
                     18.2, 15.98, 10.3, 3.13, -7.41, -12.95]  # °C
}

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# ───────────────────────────────────────────────────────────────────────────────
# 2.  Helper functions (vector-friendly, allow fractional hours)
# ───────────────────────────────────────────────────────────────────────────────
def solar_position(doy, lat, hr):
    decl = 23.45 * math.sin(math.radians(360 * (284 + doy) / 365))
    ha = 15 * (hr - 12)
    elev = math.asin(
        math.sin(math.radians(decl)) * math.sin(math.radians(lat)) +
        math.cos(math.radians(decl)) * math.cos(math.radians(lat)) * math.cos(math.radians(ha))
    )
    azim = math.atan2(
        math.sin(math.radians(ha)),
        math.cos(math.radians(ha)) * math.sin(math.radians(lat)) -
        math.tan(math.radians(decl)) * math.cos(math.radians(lat))
    )
    return math.degrees(elev), math.degrees(azim)

def poa_irradiance(ghi, tilt, surf_az, elev, azim):
    if elev <= 0:
        return 0
    cos_i = (math.sin(math.radians(elev)) * math.cos(math.radians(tilt)) +
             math.cos(math.radians(elev)) * math.sin(math.radians(tilt)) *
             math.cos(math.radians(azim - surf_az)))
    dni = ghi * max(0, cos_i) / max(0.1, math.sin(math.radians(elev)))
    return max(0, dni * cos_i + ghi * 0.1 * (1 + math.cos(math.radians(tilt))) / 2)

def module_temperature(amb, irr, noct=45):
    return amb + (noct - 20) * irr / 800

def module_power(irr, t_mod, p_nom, coeff=-0.0028):
    return p_nom * (irr / 1000) * (1 + coeff * (t_mod - 25))

def inverter_eff(dc_kw, rated_kw):
    lr = dc_kw / rated_kw
    if lr <= 0.1:
        return 0.85
    elif lr <= 0.2:
        return 0.92
    elif lr <= 0.5:
        return 0.96
    elif lr <= 0.75:
        return 0.98
    elif lr <= 1.0:
        return 0.989
    else:
        return 0.985

def shading_losses(gcr, elev):
    if elev <= 0:
        return 100
    sf = max(0, 1 - (gcr / 100) * (1 / math.tan(math.radians(max(1, elev)))))
    return (1 - sf) * 100

# ───────────────────────────────────────────────────────────────────────────────
# 3.  Five-minute simulation for a chosen date
# ───────────────────────────────────────────────────────────────────────────────
def simulate_one_day(sim_date: date, step_min=5):
    cfg = PROJECT_CONFIG
    gcr = 52.57
    month_ix = sim_date.month - 1
    ghi_day = cfg["monthly_ghi"][month_ix] / DAYS_IN_MONTH[month_ix]   # kWh/m²-day
    amb = cfg["monthly_temp"][month_ix]

    rows = []
    t = datetime.combine(sim_date, datetime.min.time())
    end = t + timedelta(days=1)

    while t < end:
        hr = t.hour + t.minute / 60
        elev, azim = solar_position(sim_date.timetuple().tm_yday,
                                    cfg["location"]["latitude"], hr)

        if elev > 0:
            poa = poa_irradiance(ghi_day, cfg["tilt_angle"], cfg["azimuth_angle"],
                                 elev, azim)
            tmod = module_temperature(amb, poa)
            pmod = module_power(poa, tmod, cfg["pv_modules"]["peak_power"])
            dc_kw = pmod * cfg["pv_modules"]["quantity"] / 1000
            dc_kw *= (1 - shading_losses(gcr, elev) / 100)
            ac_kw = dc_kw * inverter_eff(dc_kw, cfg["inverters"]["rated_power"])
            ac_kw *= 0.985 * (1 - 0.02) * (1 - 0.01)  # transformer & line losses
        else:
            poa = tmod = dc_kw = ac_kw = 0

        rows.append([t, ac_kw, dc_kw, poa, tmod])
        t += timedelta(minutes=step_min)

    return pd.DataFrame(rows, columns=["Timestamp", "AC_kW", "DC_kW",
                                      "POA_Irradiance_Wm2", "Module_Temp_C"])

# ───────────────────────────────────────────────────────────────────────────────
# 4.  Main entry point
# ───────────────────────────────────────────────────────────────────────────────
def main(sim_date=date.today()):
    df = simulate_one_day(sim_date)
    out_file = pathlib.Path("solar_out.csv")
    df.to_csv(out_file, index=False)
    print(f"Saved {len(df)} rows → {out_file}")

    # daily energy
    mwh = (df.AC_kW.sum() * 5) / 60 / 1000
    print(f"Daily AC Energy: {mwh:6.3f} MWh")

    # Plot all parameters
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(df["Timestamp"], df["AC_kW"], label="AC Power (kW)", color="tab:blue")
    ax1.plot(df["Timestamp"], df["DC_kW"], label="DC Power (kW)", color="tab:green")
    ax1.plot(df["Timestamp"], df["POA_Irradiance_Wm2"], label="POA Irradiance (W/m²)", color="tab:orange")
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Power / Irradiance")
    ax2 = ax1.twinx()
    ax2.plot(df["Timestamp"], df["Module_Temp_C"], label="Module Temp (°C)", color="tab:red", linestyle="--")
    ax2.set_ylabel("Module Temp (°C)")
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")
    plt.title("One-Day Solar PV Simulation — All Parameters")
    plt.tight_layout()
    plt.savefig("solar_out_trends.png", dpi=150)
    plt.close()

if __name__ == "__main__":
    # Example: simulate for July 11, 2025
    main(date(2025, 7, 11))
