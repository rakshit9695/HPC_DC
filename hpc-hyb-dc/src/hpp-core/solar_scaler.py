import numpy as np
import pandas as pd
import os

# Import solar project config from solar_in.py
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../renewable_intake'))
from solar_in import PROJECT_CONFIG

def get_required_solar_ac_rating(grid_supply_mw_series, solar_config):
    """
    Given a series of required grid supply (MW), and the solar config dict,
    return the minimum AC rating of the solar farm needed to meet the max grid supply.
    """
    required_ac_rating = grid_supply_mw_series.max()
    return required_ac_rating


def main():
    # Fix the path to balanced_output.csv relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.abspath(os.path.join(script_dir, '../../../../balanced_output.csv'))
    df = pd.read_csv(csv_path)
    grid_supply_mw = df['Grid_Supply_MW']

    # Get the solar farm config (from solar_in.py)
    solar_config = PROJECT_CONFIG

    # Calculate the required AC rating
    required_ac_rating = get_required_solar_ac_rating(grid_supply_mw, solar_config)
    print(f"Required solar farm AC rating to meet grid supply: {required_ac_rating:.2f} MWac")
    print(f"Current solar farm AC rating: {solar_config['rated_power_ac']} MWac")
    if required_ac_rating > solar_config['rated_power_ac']:
        print(f"Increase solar farm size by {required_ac_rating - solar_config['rated_power_ac']:.2f} MWac")
    else:
        print("Current solar farm is sufficient.")

if __name__ == "__main__":
    main() 