class Battery:
    def __init__(self, capacity_kwh, max_charge_kw, max_discharge_kw, soc_init=0.5,
                 charge_eff=0.95, discharge_eff=0.95):
        self.capacity = capacity_kwh  # in kWh
        self.max_charge = max_charge_kw  # kW
        self.max_discharge = max_discharge_kw  # kW
        self.soc = soc_init  # Initial SOC (0 to 1)
        self.charge_eff = charge_eff
        self.discharge_eff = discharge_eff

    def __str__(self):
        return (f"Battery(capacity={self.capacity}kWh, max_charge={self.max_charge}kW, "
                f"max_discharge={self.max_discharge}kW, soc={self.soc:.2f})")
