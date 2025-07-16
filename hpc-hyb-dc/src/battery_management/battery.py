import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import os

class MegawattBattery:
    def __init__(self, capacity_mwh=100, initial_charge_percent=50):
        self.capacity_mwh = capacity_mwh 
        self.current_charge = (initial_charge_percent / 100) * capacity_mwh
        self.max_charge_power = 50  # MW
        self.max_discharge_power = 50  # MW
        
        
        self.min_charge = 0.55 * capacity_mwh  
        self.max_charge_limit = 0.95 * capacity_mwh  
        
    def get_charge_percentage(self):
        return (self.current_charge / self.capacity_mwh) * 100
    
    def get_available_charge_capacity(self):
        return self.max_charge_limit - self.current_charge
    
    def get_available_discharge_capacity(self):
        return self.current_charge - self.min_charge
    
    def charge(self, power_mw, hours):
        if power_mw <= 0:
            return 0

        actual_power = min(power_mw, self.max_charge_power)
        energy_to_add = actual_power * hours

        available_capacity = self.get_available_charge_capacity()
        energy_can_add = min(energy_to_add, available_capacity)
        
        self.current_charge += energy_can_add
        return energy_can_add / hours if hours > 0 else 0
    
    def discharge(self, power_mw, hours):
        if power_mw <= 0:
            return 0
            
        actual_power = min(power_mw, self.max_discharge_power)
        energy_to_remove = actual_power * hours
        
        available_energy = self.get_available_discharge_capacity()
        energy_can_remove = min(energy_to_remove, available_energy)
        
        self.current_charge -= energy_can_remove
        return energy_can_remove / hours if hours > 0 else 0  

class MegawattDataCenter:
    def __init__(self, base_power_mw=50):
        self.base_power_mw = base_power_mw
    
    def get_power_needed(self, hour_of_day):
     
        if 8 <= hour_of_day <= 18: 
            return self.base_power_mw * 1.2  
        else:  
            return self.base_power_mw 

class ExcessEnergyReader:
    
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.excess_data = None
        self.load_excess_data()
    
    def load_excess_data(self):
      
        try:
            
            self.excess_data = pd.read_csv(self.csv_file_path)
            
            self.excess_data['Timestamp'] = pd.to_datetime(self.excess_data['Timestamp'])
            
 
            self.excess_data = self.excess_data.sort_values('Timestamp')
            
            print(f"Loaded excess energy data")
            print(f"Data points: {len(self.excess_data)}")
            print(f"Time range: {self.excess_data['Timestamp'].iloc[0]} to {self.excess_data['Timestamp'].iloc[-1]}")
            print(f"Max excess energy: {self.excess_data['Excess_MW'].max():.2f} MW")
            print(f"Average excess energy: {self.excess_data['Excess_MW'].mean():.2f} MW")
            
        except Exception as e:
            print(f"Error loading excess energy data: {e}")
            self.excess_data = None
    
    def get_excess_energy_for_interval(self, interval_index):
        if self.excess_data is None:
            return 0
        
        try:
            if interval_index >= len(self.excess_data):
            
                interval_index = interval_index % len(self.excess_data)
            
            return max(0, self.excess_data['Excess_MW'].iloc[interval_index])
            
        except Exception as e:
            print(f"Error getting excess energy for interval {interval_index}: {e}")
            return 0

class RealTimeBMS:
    
    def __init__(self, battery, datacenter, excess_reader):
        self.battery = battery
        self.datacenter = datacenter
        self.excess_reader = excess_reader
        
        
        self.time_interval = 5 / 60 
        
        
        self.cheap_electricity_hours = [0, 1, 2, 3, 4, 5, 23]  
        self.expensive_electricity_hours = [17, 18, 19, 20, 21]  
        
       
        self.history = {
            'time_minutes': [],
            'time_hours': [],
            'battery_charge_mwh': [],
            'battery_charge_percent': [],
            'power_needed_mw': [],
            'excess_energy_mw': [],
            'battery_power_mw': [],  
            'grid_power_mw': [],
            'unused_excess_mw': [],
            'action': []
        }
    
    def make_realtime_decision(self, interval_index):
       
        current_hour = (interval_index * 5 / 60) % 24  
        power_needed = self.datacenter.get_power_needed(int(current_hour))
        excess_energy = self.excess_reader.get_excess_energy_for_interval(interval_index)
        
        battery_power = 0  
        grid_power = 0
        unused_excess = 0
        action = "idle"
        
        
        if excess_energy > 0:
            if excess_energy >= power_needed:
                remaining_excess = excess_energy - power_needed
                grid_power = 0
                
                if remaining_excess > 0 and self.battery.get_charge_percentage() < 90:
                    charge_power = min(remaining_excess, self.battery.max_charge_power)
                    actual_charge_power = self.battery.charge(charge_power, self.time_interval)
                    battery_power = -actual_charge_power  
                    unused_excess = remaining_excess - actual_charge_power
                    action = "charging_excess"
                else:
                    unused_excess = remaining_excess
                    action = "excess_covers_load"
            else:
                remaining_load = power_needed - excess_energy
                
                if int(current_hour) in self.expensive_electricity_hours and \
                   self.battery.get_charge_percentage() > 10:
                    discharge_power = min(remaining_load, self.battery.max_discharge_power)
                    actual_discharge_power = self.battery.discharge(discharge_power, self.time_interval)
                    battery_power = actual_discharge_power  
                    grid_power = remaining_load - actual_discharge_power
                    action = "discharging_peak"
                else:
                    grid_power = remaining_load
                    action = "grid_supplement"
        else:
            if int(current_hour) in self.expensive_electricity_hours and \
               self.battery.get_charge_percentage() > 15:
                discharge_power = min(power_needed, self.battery.max_discharge_power)
                actual_discharge_power = self.battery.discharge(discharge_power, self.time_interval)
                battery_power = actual_discharge_power
                grid_power = power_needed - actual_discharge_power
                action = "discharging_peak"
            elif int(current_hour) in self.cheap_electricity_hours and \
                 self.battery.get_charge_percentage() < 80:
                available_charge_capacity = self.battery.get_available_charge_capacity()
                charge_power = min(20, self.battery.max_charge_power)  # 20 MW charge rate
                actual_charge_power = self.battery.charge(charge_power, self.time_interval)
                battery_power = -actual_charge_power
                grid_power = power_needed + actual_charge_power
                action = "charging_cheap"
            else:
                grid_power = power_needed
                action = "grid_only"
        
        return (action, battery_power, grid_power, power_needed, 
                excess_energy, unused_excess)
    
    def run_realtime_simulation(self, hours=24):
        """Run real-time simulation with 5-minute intervals"""
        print(f"Starting real-time simulation for {hours} hours (5-minute intervals)...")
        print(f"Initial battery charge: {self.battery.get_charge_percentage():.1f}%")
        print(f"Battery capacity: {self.battery.capacity_mwh} MWh")
        print(f"Data center base load: {self.datacenter.base_power_mw} MW")
        print("-" * 80)
        
        total_intervals = hours * 12
        
        total_excess_available = 0
        total_excess_used = 0
        total_grid_energy = 0
        total_battery_charge_energy = 0
        total_battery_discharge_energy = 0
        
        for interval in range(total_intervals):
            
            action, battery_power, grid_power, power_needed, excess_energy, unused_excess = \
                self.make_realtime_decision(interval)
            
            excess_energy_interval = excess_energy * self.time_interval
            grid_energy_interval = grid_power * self.time_interval
            
            
            total_excess_available += excess_energy_interval
            total_excess_used += (excess_energy - unused_excess) * self.time_interval
            total_grid_energy += grid_energy_interval
            
            if battery_power < 0:  
                total_battery_charge_energy += abs(battery_power) * self.time_interval
            elif battery_power > 0: 
                total_battery_discharge_energy += battery_power * self.time_interval
            
            
            current_time_minutes = interval * 5
            current_time_hours = current_time_minutes / 60
            
            self.history['time_minutes'].append(current_time_minutes)
            self.history['time_hours'].append(current_time_hours)
            self.history['battery_charge_mwh'].append(self.battery.current_charge)
            self.history['battery_charge_percent'].append(self.battery.get_charge_percentage())
            self.history['power_needed_mw'].append(power_needed)
            self.history['excess_energy_mw'].append(excess_energy)
            self.history['battery_power_mw'].append(battery_power)
            self.history['grid_power_mw'].append(grid_power)
            self.history['unused_excess_mw'].append(unused_excess)
            self.history['action'].append(action)
            
            
            if interval % 12 == 0:
                hour = interval // 12
                print(f"Hour {hour:2d}: Battery {self.battery.get_charge_percentage():5.1f}% "
                      f"({self.battery.current_charge:.1f} MWh) | "
                      f"Excess: {excess_energy:6.1f}MW | Action: {action:15s} | "
                      f"Load: {power_needed:5.1f}MW | Grid: {grid_power:5.1f}MW")
        
        print("-" * 80)
        print("Real-time simulation completed!")
        print(f"Final battery charge: {self.battery.get_charge_percentage():.1f}% "
              f"({self.battery.current_charge:.1f} MWh)")
        
        
        total_load_energy = sum([p * self.time_interval for p in self.history['power_needed_mw']])
        
        print(f"\nENERGY SUMMARY:")
        print(f"Total load energy needed: {total_load_energy:.1f} MWh")
        print(f"Total excess energy available: {total_excess_available:.1f} MWh")
        print(f"Total excess energy used: {total_excess_used:.1f} MWh")
        print(f"Total grid energy used: {total_grid_energy:.1f} MWh")
        print(f"Total battery charged: {total_battery_charge_energy:.1f} MWh")
        print(f"Total battery discharged: {total_battery_discharge_energy:.1f} MWh")
        
        if total_excess_available > 0:
            excess_utilization = (total_excess_used / total_excess_available) * 100
            print(f"Excess energy utilization: {excess_utilization:.1f}%")
        
        renewable_percentage = (total_excess_used / total_load_energy) * 100
        print(f"Renewable energy percentage: {renewable_percentage:.1f}%")
        
        
        if total_battery_charge_energy > 0:
            battery_efficiency = (total_battery_discharge_energy / total_battery_charge_energy) * 100
            print(f"Battery round-trip efficiency: {battery_efficiency:.1f}%")
    
    def plot_realtime_results(self):
        """Create detailed plots for real-time simulation results"""
        if not self.history['time_hours']:
            print("No data to plot!")
            return
        
        fig, axes = plt.subplots(3, 2, figsize=(18, 14))
        fig.suptitle('Real-Time Battery Management System with Excess Energy', fontsize=16)
        
        
        axes[0,0].plot(self.history['time_hours'], self.history['battery_charge_mwh'], 
                       'b-', linewidth=2, label='Battery Charge')
        axes[0,0].axhline(y=self.battery.min_charge, color='r', linestyle='--', 
                          alpha=0.7, label=f'Min ({self.battery.min_charge:.1f} MWh)')
        axes[0,0].axhline(y=self.battery.max_charge_limit, color='r', linestyle='--', 
                          alpha=0.7, label=f'Max ({self.battery.max_charge_limit:.1f} MWh)')
        axes[0,0].set_xlabel('Time (hours)')
        axes[0,0].set_ylabel('Battery Charge (MWh)')
        axes[0,0].set_title('Battery Charge Over Time')
        axes[0,0].grid(True, alpha=0.3)
        axes[0,0].legend()
        
        axes[0,1].plot(self.history['time_hours'], self.history['power_needed_mw'], 
                       'k-', linewidth=2, label='Load Required')
        axes[0,1].plot(self.history['time_hours'], self.history['excess_energy_mw'], 
                       'g-', linewidth=2, label='Excess Available')
        axes[0,1].plot(self.history['time_hours'], self.history['grid_power_mw'], 
                       'r-', linewidth=2, label='Grid Power')
        axes[0,1].fill_between(self.history['time_hours'], self.history['excess_energy_mw'], 
                               alpha=0.3, color='green', label='Excess Energy')
        axes[0,1].set_xlabel('Time (hours)')
        axes[0,1].set_ylabel('Power (MW)')
        axes[0,1].set_title('Power Flows')
        axes[0,1].grid(True, alpha=0.3)
        axes[0,1].legend()
        
        axes[1,0].plot(self.history['time_hours'], self.history['battery_charge_percent'], 
                       'purple', linewidth=2)
        axes[1,0].axhline(y=5, color='r', linestyle='--', alpha=0.7, label='Min 5%')
        axes[1,0].axhline(y=95, color='r', linestyle='--', alpha=0.7, label='Max 95%')
        axes[1,0].set_xlabel('Time (hours)')
        axes[1,0].set_ylabel('Battery Charge (%)')
        axes[1,0].set_title('Battery State of Charge')
        axes[1,0].grid(True, alpha=0.3)
        axes[1,0].legend()
        
        charging_power = [-p if p < 0 else 0 for p in self.history['battery_power_mw']]
        discharging_power = [p if p > 0 else 0 for p in self.history['battery_power_mw']]
        
        axes[1,1].fill_between(self.history['time_hours'], charging_power, 
                               alpha=0.6, color='blue', label='Charging')
        axes[1,1].fill_between(self.history['time_hours'], discharging_power, 
                               alpha=0.6, color='orange', label='Discharging')
        axes[1,1].set_xlabel('Time (hours)')
        axes[1,1].set_ylabel('Battery Power (MW)')
        axes[1,1].set_title('Battery Charging/Discharging')
        axes[1,1].grid(True, alpha=0.3)
        axes[1,1].legend()
        
        axes[2,0].plot(self.history['time_hours'], self.history['excess_energy_mw'], 
                       'g-', linewidth=2, label='Available')
        axes[2,0].plot(self.history['time_hours'], self.history['unused_excess_mw'], 
                       'orange', linewidth=2, label='Unused')
        axes[2,0].fill_between(self.history['time_hours'], self.history['unused_excess_mw'], 
                               alpha=0.4, color='orange')
        axes[2,0].set_xlabel('Time (hours)')
        axes[2,0].set_ylabel('Excess Energy (MW)')
        axes[2,0].set_title('Excess Energy Utilization')
        axes[2,0].grid(True, alpha=0.3)
        axes[2,0].legend()
        
        total_intervals = len(self.history['time_hours'])
        excess_used = [ex - un for ex, un in zip(self.history['excess_energy_mw'], 
                                                  self.history['unused_excess_mw'])]
        
        axes[2,1].fill_between(self.history['time_hours'], excess_used, 
                               alpha=0.7, color='green', label='Excess Energy')
        axes[2,1].fill_between(self.history['time_hours'], 
                               [ex + gr for ex, gr in zip(excess_used, self.history['grid_power_mw'])], 
                               excess_used, alpha=0.7, color='red', label='Grid Power')
        axes[2,1].set_xlabel('Time (hours)')
        axes[2,1].set_ylabel('Power (MW)')
        axes[2,1].set_title('Energy Sources Over Time')
        axes[2,1].grid(True, alpha=0.3)
        axes[2,1].legend()
        
        plt.tight_layout()
        plt.show()

def get_user_configuration():
    print("\n=== REAL-TIME BATTERY MANAGEMENT SYSTEM CONFIGURATION ===")
    print("Battery Management System with Excess Energy CSV Integration!\n")
    
    while True:
        try:
            capacity = float(input("Enter battery capacity (MWh) [default: 100]: ") or "100")
            if capacity > 0:
                break
            else:
                print("Please enter a positive number for capacity.")
        except ValueError:
            print("Please enter a valid number for capacity.")
    
    while True:
        try:
            initial_charge_percent = float(input("Enter initial charge percentage [default: 50]: ") or "50")
            if 0 <= initial_charge_percent <= 100:
                break
            else:
                print("Initial charge percentage must be between 0 and 100.")
        except ValueError:
            print("Please enter a valid number for initial charge percentage.")
    
    while True:
        try:
            datacenter_power = float(input("Enter data center base power consumption (MW) [default: 50]: ") or "50")
            if datacenter_power > 0:
                break
            else:
                print("Please enter a positive number for power consumption.")
        except ValueError:
            print("Please enter a valid number for power consumption.")
    
    while True:
        try:
            hours = int(input("Enter simulation duration (hours) [default: 24]: ") or "24")
            if hours > 0:
                break
            else:
                print("Please enter a positive number of hours.")
        except ValueError:
            print("Please enter a valid number for hours.")
    
    return capacity, initial_charge_percent, datacenter_power, hours

def display_configuration(capacity, initial_charge_percent, datacenter_power, hours):
    """Display the system configuration"""
    print("\n" + "="*60)
    print("REAL-TIME SYSTEM CONFIGURATION")
    print("="*60)
    print(f"Battery Capacity:           {capacity} MWh")
    print(f"Initial Charge:             {initial_charge_percent}% ({capacity * initial_charge_percent / 100:.1f} MWh)")
    print(f"Data Center Base Power:     {datacenter_power} MW")
    print(f"Simulation Duration:        {hours} hours")
    print(f"Time Resolution:            5 minutes")
    print("="*60)
    
    print("\nBATTERY SPECIFICATIONS:")
    print(f"- Maximum charging power:   50 MW")
    print(f"- Maximum discharging power: 50 MW")
    print(f"- Safe operating range:     5% - 95% ({capacity*0.05:.1f} - {capacity*0.95:.1f} MWh)")
    print(f"- Continuous operation:     Battery never fully discharges")
    
    print("\nREAL-TIME OPERATION:")
    print("- 5-minute decision intervals")
    print("- Excess energy prioritized for charging")
    print("- Smart grid interaction based on electricity pricing")
    print("- Continuous battery state monitoring")
    print("="*60)


if __name__ == "__main__":
    print("=== REAL-TIME BATTERY MANAGEMENT SYSTEM ===")
    print("With Excess Energy CSV Integration (5-minute resolution)\n")
    
    csv_file = "excess_energy_output.csv"
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        print("Please ensure the excess energy CSV file is in the current directory.")
        exit()
    
    excess_reader = ExcessEnergyReader(csv_file)
    if excess_reader.excess_data is None:
        print("Failed to load excess energy data. Exiting.")
        exit()
    
    capacity, initial_charge_percent, datacenter_power, hours = get_user_configuration()
    
    display_configuration(capacity, initial_charge_percent, datacenter_power, hours)
    
    # Ask for confirmation
    print("\nReady to run real-time simulation with excess energy data?")
    confirm = input("Press Enter to continue or 'q' to quit: ").lower()
    
    if confirm == 'q':
        print("Simulation cancelled. Goodbye!")
        exit()
    
    print("\n" + "="*60)
    print("STARTING REAL-TIME SIMULATION")
    print("="*60)
    
    battery = MegawattBattery(capacity_mwh=capacity, initial_charge_percent=initial_charge_percent)
    datacenter = MegawattDataCenter(base_power_mw=datacenter_power)
    
    bms = RealTimeBMS(battery, datacenter, excess_reader)
    
    bms.run_realtime_simulation(hours=hours)
    
    print("\nWould you like to see the results graphically?")
    show_plots = input("Press Enter for yes, or 'n' for no: ").lower()
    
    if show_plots != 'n':
        print("Generating real-time simulation plots...")
        bms.plot_realtime_results()
    
    print("\n=== REAL-TIME SYSTEM EXPLANATION ===")
    print("What happened in the real-time simulation:")
    print("1. System operates with 5-minute decision intervals")
    print("2. Excess energy directly charges battery when available")
    print("3. Battery provides power during peak pricing hours")
    print("4. Grid power used as backup when needed")
    print("5. Battery maintains safe operating range (5%-95%)")
    print("6. Continuous operation ensures system reliability")
    print("\nThank you for using the Real-Time Battery Management System!")