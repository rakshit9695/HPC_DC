import csv
import pandas as pd
import matplotlib.pyplot as plt

# File paths (update as needed)
WIND_FILE  = "/Users/rakshit9695/Desktop/Final_Implementation/Final_Implementation/hpc-hyb-dc/src/hpp-core/csv_files/wind_farm_hpc_max_output.csv"
LOAD_FILE  = "/Users/rakshit9695/Desktop/Final_Implementation/Final_Implementation/hpc-hyb-dc/src/hpp-core/csv_files/dc_10MW_load_profile.csv"

def load_csv_with_csv_module(file_path):
    """Load CSV file using csv.reader and return as list of dicts."""
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        data = [row for row in reader]
    return data

def load_and_merge(wind_f, load_f):
    df_w = pd.read_csv(wind_f, parse_dates=["Timestamp"])
    load_data = load_csv_with_csv_module(load_f)
    df_l = pd.DataFrame(load_data)
    df_l["Timestamp"] = pd.to_datetime(df_l["Timestamp"])
    df_l["Load_kW"] = pd.to_numeric(df_l["Load_kW"], errors="coerce")

    wind_col = next((col for col in df_w.columns if "HPC_Max_MW" in col or "AC_Power_MW" in col), None)
    if wind_col is None:
        raise ValueError(f"Could not find wind power column. Wind columns: {df_w.columns}")
    print(f"Detected wind column: {wind_col}")
    df_w = df_w.rename(columns={wind_col: "Wind_MW"})

    df = df_l.merge(df_w[["Timestamp", "Wind_MW"]], on="Timestamp", how="left")
    df["Wind_MW"] = df["Wind_MW"].fillna(0)
    return df

def add_grid_profile(df):
    df["Grid_Capability_MW"] = 100.0
    return df

def balance(df):
    df["Load_MW"] = df["Load_kW"] / 1000.0
    df["Excess_MW"] = (df["Wind_MW"] - df["Load_MW"]).clip(lower=0)
    df["Deficit_MW"] = (df["Load_MW"] - df["Wind_MW"]).clip(lower=0)
    df["Grid_Supply_MW"] = df["Deficit_MW"]
    return df

def plot_load_vs_supply(df):
    ts = df["Timestamp"]
    plt.figure(figsize=(12,5))
    plt.plot(ts, df["Load_MW"], label="HPC Load", color="black", linewidth=1.5)
    plt.fill_between(ts, df["Wind_MW"], label="Wind", color="skyblue", alpha=0.6)
    plt.fill_between(ts,
                     df["Wind_MW"],
                     df["Wind_MW"] + df["Grid_Supply_MW"],
                     label="Grid", color="lightcoral", alpha=0.6)
    plt.legend(loc="upper left")
    plt.title("Load vs Supply Breakdown (Wind + Grid)")
    plt.ylabel("Power (MW)")
    plt.xlabel("Timestamp")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("plot_load_vs_supply.png")
    plt.close()

def plot_wind(df):
    ts = df["Timestamp"]
    plt.figure(figsize=(12,4))
    plt.plot(ts, df["Wind_MW"],  label="Wind",  color="blue", linewidth=1)
    plt.legend()
    plt.title("Wind Output")
    plt.ylabel("Power (MW)")
    plt.xlabel("Timestamp")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("plot_wind.png")
    plt.close()

def plot_excess(df):
    ts = df["Timestamp"]
    plt.figure(figsize=(12,4))
    plt.plot(ts, df["Excess_MW"], color="green", linewidth=1)
    plt.title("Excess Wind Power")
    plt.ylabel("Power (MW)")
    plt.xlabel("Timestamp")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("plot_excess.png")
    plt.close()

def plot_grid_dependency(df):
    ts = df["Timestamp"]
    plt.figure(figsize=(12,4))
    plt.plot(ts, df["Grid_Supply_MW"], color="red", linewidth=1)
    plt.title("Grid Supply Requirement")
    plt.ylabel("Power (MW)")
    plt.xlabel("Timestamp")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("plot_grid_dependency.png")
    plt.close()

def output_excess_energy_csv(df, filename="excess_energy_output.csv"):
    """Output CSV with only Timestamp and Excess_MW columns."""
    excess_df = df[["Timestamp", "Excess_MW"]].copy()
    excess_df.to_csv(filename, index=False)
    print(f"Excess energy output saved to {filename}")

def main():
    df = load_and_merge(WIND_FILE, LOAD_FILE)
    df = add_grid_profile(df)
    df = balance(df)
    df.to_csv("balanced_output.csv", index=False)
    print("Balanced output saved to balanced_output.csv")
    output_excess_energy_csv(df, filename="excess_energy_output.csv")
    plot_load_vs_supply(df)
    plot_wind(df)
    plot_excess(df)
    plot_grid_dependency(df)
    print("Plots saved as PNG files.")

if __name__ == "__main__":
    main()
