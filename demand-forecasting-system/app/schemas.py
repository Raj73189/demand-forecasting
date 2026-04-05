from dataclasses import dataclass


@dataclass
class HorizonDemand:
    forecast: float
    is_high_demand: bool
