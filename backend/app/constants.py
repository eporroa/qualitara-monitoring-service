ZONES = [
    "inbound_dock_a",
    "inbound_dock_b",
    "receiving_staging",
    "aisle_a",
    "aisle_b",
    "aisle_c",
    "high_bay_1",
    "high_bay_2",
    "bulk_storage",
    "pick_zone_1",
    "pick_zone_2",
    "pack_station",
    "sort_belt",
    "outbound_dock_a",
    "outbound_dock_b",
    "shipping_staging",
    "charging_bay_1",
    "charging_bay_2",
    "charging_bay_3",
    "maintenance_bay",
]

VEHICLE_IDS = [f"v-{i}" for i in range(1, 51)]

ANOMALY_RULES = {
    "battery_critical": {"field": "battery_pct", "op": "lt", "threshold": 10},
    "battery_low": {"field": "battery_pct", "op": "lt", "threshold": 20},
    "overspeed": {"field": "speed_mps", "op": "gt", "threshold": 5.0},
}
