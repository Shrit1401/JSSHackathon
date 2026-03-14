from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone, timedelta

MANUFACTURERS = {
    "camera": ["Hikvision", "Dahua", "Reolink", "Amcrest"],
    "printer": ["HP", "Brother", "Canon", "Epson"],
    "router": ["Cisco", "Ubiquiti", "TP-Link", "MikroTik"],
    "laptop": ["Dell", "Lenovo", "Apple", "HP"],
    "smart_tv": ["Samsung", "LG", "Sony", "TCL"],
    "thermostat": ["Nest", "Ecobee", "Honeywell"],
    "smart_door_lock": ["August", "Yale", "Schlage"],
    "smart_light_hub": ["Philips Hue", "IKEA Tradfri", "Lutron"],
    "temperature_sensor": ["Aqara", "Xiaomi", "Sonoff"],
    "network_gateway": ["Cisco", "Ubiquiti", "Sierra Wireless"],
}

FIRMWARE = {
    "camera": ["v4.1.2", "v4.0.8", "v3.9.1"],
    "printer": ["fw2024.03", "fw2023.11", "fw2024.06"],
    "router": ["v7.14.3", "v7.12.0", "v6.49.10"],
    "laptop": ["BIOS 1.22", "BIOS 1.18", "BIOS 2.01"],
    "smart_tv": ["T-KTSUAKUC-1302.5", "webOS 24.1", "Android TV 14"],
    "thermostat": ["6.2.0-rc3", "5.9.3", "6.0.1"],
    "smart_door_lock": ["v1.62.0", "v1.58.2", "v2.0.1"],
    "smart_light_hub": ["1.65.0", "2.3.0", "1.54.2"],
    "temperature_sensor": ["0.12.4", "0.11.8", "1.0.0"],
    "network_gateway": ["ER-v2.0.9", "USG-v5.0.3", "RV-v1.0.3"],
}

MAC_PREFIXES = {
    "camera": "AA:BB:CC",
    "printer": "DD:EE:FF",
    "router": "00:11:22",
    "laptop": "33:44:55",
    "smart_tv": "66:77:88",
    "thermostat": "99:AA:BB",
    "smart_door_lock": "CC:DD:EE",
    "smart_light_hub": "FF:00:11",
    "temperature_sensor": "22:33:44",
    "network_gateway": "55:66:77",
}


def _mac(prefix: str, idx: int) -> str:
    return f"{prefix}:{idx:02X}:{random.randint(0, 255):02X}:{random.randint(0, 255):02X}"


def _pick(lst: list) -> str:
    return random.choice(lst)


DEVICE_FLEET = [
    {"name": "gateway_1",      "type": "network_gateway",   "ip": "192.168.1.254"},
    {"name": "router_1",       "type": "router",            "ip": "192.168.1.1"},
    {"name": "router_2",       "type": "router",            "ip": "192.168.1.2"},
    {"name": "laptop_1",       "type": "laptop",            "ip": "192.168.1.50"},
    {"name": "laptop_2",       "type": "laptop",            "ip": "192.168.1.51"},
    {"name": "laptop_3",       "type": "laptop",            "ip": "192.168.1.52"},
    {"name": "laptop_4",       "type": "laptop",            "ip": "192.168.1.53"},
    {"name": "camera_1",       "type": "camera",            "ip": "192.168.1.101"},
    {"name": "camera_2",       "type": "camera",            "ip": "192.168.1.102"},
    {"name": "camera_3",       "type": "camera",            "ip": "192.168.1.103"},
    {"name": "camera_4",       "type": "camera",            "ip": "192.168.1.104"},
    {"name": "camera_5",       "type": "camera",            "ip": "192.168.1.105"},
    {"name": "printer_1",      "type": "printer",           "ip": "192.168.1.201"},
    {"name": "printer_2",      "type": "printer",           "ip": "192.168.1.202"},
    {"name": "printer_3",      "type": "printer",           "ip": "192.168.1.203"},
    {"name": "smart_tv_1",     "type": "smart_tv",          "ip": "192.168.1.150"},
    {"name": "smart_tv_2",     "type": "smart_tv",          "ip": "192.168.1.151"},
    {"name": "smart_tv_3",     "type": "smart_tv",          "ip": "192.168.1.152"},
    {"name": "light_hub_1",    "type": "smart_light_hub",   "ip": "192.168.1.190"},
    {"name": "light_hub_2",    "type": "smart_light_hub",   "ip": "192.168.1.191"},
    {"name": "thermostat_1",   "type": "thermostat",        "ip": "192.168.1.170"},
    {"name": "thermostat_2",   "type": "thermostat",        "ip": "192.168.1.171"},
    {"name": "door_lock_1",    "type": "smart_door_lock",   "ip": "192.168.1.180"},
    {"name": "door_lock_2",    "type": "smart_door_lock",   "ip": "192.168.1.181"},
    {"name": "temp_sensor_1",  "type": "temperature_sensor","ip": "192.168.1.210"},
    {"name": "temp_sensor_2",  "type": "temperature_sensor","ip": "192.168.1.211"},
    {"name": "temp_sensor_3",  "type": "temperature_sensor","ip": "192.168.1.212"},
]

# ═══════════════════════════════════════════
#  HIERARCHICAL TOPOLOGY
#
#  source = parent device
#  target = child device
#
#  Network Gateway (gateway_1)
#  ├── Router 1 (router_1)                  backbone
#  │   ├── Laptop 1 (laptop_1)              wifi
#  │   │   └── Smart TV 1 (smart_tv_1)      wifi_bridge
#  │   ├── Laptop 2 (laptop_2)              wifi
#  │   ├── Camera 1 (camera_1)              ethernet
#  │   ├── Camera 2 (camera_2)              ethernet
#  │   └── Printer 1 (printer_1)            ethernet
#  │
#  ├── Router 2 (router_2)                  backbone
#  │   ├── Laptop 3 (laptop_3)              wifi
#  │   ├── Laptop 4 (laptop_4)              wifi
#  │   │   └── Smart TV 3 (smart_tv_3)      wifi_bridge
#  │   ├── Smart TV 2 (smart_tv_2)          wifi
#  │   ├── Camera 3 (camera_3)              ethernet
#  │   └── Printer 2 (printer_2)            ethernet
#  │
#  ├── Light Hub 1 (light_hub_1)            ethernet
#  │   ├── Thermostat 1 (thermostat_1)      zigbee
#  │   ├── Temp Sensor 1 (temp_sensor_1)    zigbee
#  │   └── Door Lock 1 (door_lock_1)        zigbee
#  │
#  ├── Light Hub 2 (light_hub_2)            ethernet
#  │   ├── Thermostat 2 (thermostat_2)      zigbee
#  │   ├── Temp Sensor 2 (temp_sensor_2)    zigbee
#  │   └── Door Lock 2 (door_lock_2)        zigbee
#  │
#  ├── Camera 4 (camera_4)                  ethernet
#  ├── Camera 5 (camera_5)                  ethernet
#  ├── Printer 3 (printer_3)                ethernet
#  └── Temp Sensor 3 (temp_sensor_3)        coap
# ═══════════════════════════════════════════

TOPOLOGY_EDGES = [
    ("gateway_1",   "router_1",       "backbone"),
    ("gateway_1",   "router_2",       "backbone"),
    ("gateway_1",   "light_hub_1",    "ethernet"),
    ("gateway_1",   "light_hub_2",    "ethernet"),
    ("gateway_1",   "camera_4",       "ethernet"),
    ("gateway_1",   "camera_5",       "ethernet"),
    ("gateway_1",   "printer_3",      "ethernet"),
    ("gateway_1",   "temp_sensor_3",  "coap"),

    ("router_1",    "laptop_1",       "wifi"),
    ("router_1",    "laptop_2",       "wifi"),
    ("router_1",    "camera_1",       "ethernet"),
    ("router_1",    "camera_2",       "ethernet"),
    ("router_1",    "printer_1",      "ethernet"),

    ("router_2",    "laptop_3",       "wifi"),
    ("router_2",    "laptop_4",       "wifi"),
    ("router_2",    "smart_tv_2",     "wifi"),
    ("router_2",    "camera_3",       "ethernet"),
    ("router_2",    "printer_2",      "ethernet"),

    ("laptop_1",    "smart_tv_1",     "wifi_bridge"),
    ("laptop_4",    "smart_tv_3",     "wifi_bridge"),

    ("light_hub_1", "thermostat_1",   "zigbee"),
    ("light_hub_1", "temp_sensor_1",  "zigbee"),
    ("light_hub_1", "door_lock_1",    "zigbee"),

    ("light_hub_2", "thermostat_2",   "zigbee"),
    ("light_hub_2", "temp_sensor_2",  "zigbee"),
    ("light_hub_2", "door_lock_2",    "zigbee"),
]


INITIAL_TRUST_PROFILES = {
    "gateway_1":     {"trust": 98.0,  "risk": "SAFE"},
    "router_1":      {"trust": 96.5,  "risk": "SAFE"},
    "router_2":      {"trust": 95.0,  "risk": "SAFE"},
    "laptop_1":      {"trust": 88.2,  "risk": "SAFE"},
    "laptop_2":      {"trust": 92.0,  "risk": "SAFE"},
    "laptop_3":      {"trust": 74.5,  "risk": "LOW"},
    "laptop_4":      {"trust": 85.3,  "risk": "SAFE"},
    "camera_1":      {"trust": 42.1,  "risk": "MEDIUM"},
    "camera_2":      {"trust": 91.7,  "risk": "SAFE"},
    "camera_3":      {"trust": 28.5,  "risk": "HIGH"},
    "camera_4":      {"trust": 97.0,  "risk": "SAFE"},
    "camera_5":      {"trust": 89.3,  "risk": "SAFE"},
    "printer_1":     {"trust": 95.0,  "risk": "SAFE"},
    "printer_2":     {"trust": 100.0, "risk": "SAFE"},
    "printer_3":     {"trust": 63.0,  "risk": "LOW"},
    "smart_tv_1":    {"trust": 55.0,  "risk": "MEDIUM"},
    "smart_tv_2":    {"trust": 81.0,  "risk": "SAFE"},
    "smart_tv_3":    {"trust": 70.5,  "risk": "LOW"},
    "light_hub_1":   {"trust": 99.0,  "risk": "SAFE"},
    "light_hub_2":   {"trust": 97.5,  "risk": "SAFE"},
    "thermostat_1":  {"trust": 100.0, "risk": "SAFE"},
    "thermostat_2":  {"trust": 94.0,  "risk": "SAFE"},
    "door_lock_1":   {"trust": 100.0, "risk": "SAFE"},
    "door_lock_2":   {"trust": 98.0,  "risk": "SAFE"},
    "temp_sensor_1": {"trust": 100.0, "risk": "SAFE"},
    "temp_sensor_2": {"trust": 100.0, "risk": "SAFE"},
    "temp_sensor_3": {"trust": 90.0,  "risk": "SAFE"},
}


SAMPLE_ALERTS = [
    {"device": "camera_3",   "type": "ML_ANOMALY",       "severity": "CRITICAL", "desc": "Isolation Forest flagged camera_3 with anomaly score 0.92 — massive outbound data spike to external IP"},
    {"device": "camera_3",   "type": "POLICY_VIOLATION",  "severity": "HIGH",     "desc": "camera_3 using SSH protocol — blocked by CAM-PROTO-001"},
    {"device": "camera_3",   "type": "DRIFT_CONFIRMED",   "severity": "HIGH",     "desc": "Behavioral drift confirmed on camera_3 — 5 consecutive anomalous windows"},
    {"device": "camera_3",   "type": "TRUST_DROP",        "severity": "CRITICAL", "desc": "Trust score dropped to 28.5 (HIGH risk)"},
    {"device": "camera_1",   "type": "ML_ANOMALY",       "severity": "HIGH",     "desc": "Isolation Forest flagged camera_1 with anomaly score 0.71 — elevated outbound traffic"},
    {"device": "camera_1",   "type": "DRIFT_DETECTED",    "severity": "MEDIUM",   "desc": "Behavioral drift detected on camera_1 — traffic_volume z-score exceeded threshold"},
    {"device": "smart_tv_1", "type": "POLICY_VIOLATION",  "severity": "HIGH",     "desc": "smart_tv_1 contacted unknown external destination — blocked by STV-DEST-001"},
    {"device": "smart_tv_1", "type": "TRUST_DROP",        "severity": "HIGH",     "desc": "Trust score dropped to 55.0 (MEDIUM risk)"},
    {"device": "printer_3",  "type": "POLICY_VIOLATION",  "severity": "MEDIUM",   "desc": "printer_3 bytes_sent exceeded 50KB ceiling — PRT-TRAF-001"},
    {"device": "laptop_3",   "type": "DRIFT_DETECTED",    "severity": "LOW",      "desc": "Mild behavioral drift on laptop_3 — destination_entropy slightly elevated"},
]


TRUST_HISTORY_ENTRIES = [
    {"device": "camera_3", "scores": [95.0, 82.0, 68.0, 51.0, 35.0, 28.5], "reasons": [
        "nominal", "ml_penalty=7.2", "ml_penalty=12.8, drift_penalty=6.0",
        "ml_penalty=19.6, drift_penalty=10.4, policy_penalty=10.0",
        "ml_penalty=26.0, drift_penalty=14.0, policy_penalty=15.0",
        "ml_penalty=28.6, drift_penalty=17.9, policy_penalty=25.0",
    ]},
    {"device": "camera_1", "scores": [100.0, 94.0, 78.0, 55.0, 42.1], "reasons": [
        "nominal", "ml_penalty=6.0", "ml_penalty=10.0, drift_penalty=4.0",
        "ml_penalty=18.0, drift_penalty=12.0, policy_penalty=15.0",
        "ml_penalty=22.3, drift_penalty=15.6, policy_penalty=20.0",
    ]},
    {"device": "smart_tv_1", "scores": [100.0, 88.0, 72.0, 55.0], "reasons": [
        "nominal", "policy_penalty=12.0",
        "ml_penalty=8.0, policy_penalty=20.0",
        "ml_penalty=15.0, drift_penalty=10.0, policy_penalty=20.0",
    ]},
    {"device": "printer_3", "scores": [100.0, 90.0, 75.0, 63.0], "reasons": [
        "nominal", "policy_penalty=10.0",
        "ml_penalty=5.0, policy_penalty=20.0",
        "ml_penalty=12.0, policy_penalty=25.0",
    ]},
    {"device": "laptop_3", "scores": [100.0, 92.0, 82.0, 74.5], "reasons": [
        "nominal", "ml_penalty=8.0",
        "ml_penalty=10.0, drift_penalty=8.0",
        "ml_penalty=12.5, drift_penalty=10.0, policy_penalty=3.0",
    ]},
]


PROTOCOLS_BY_TYPE = {
    "camera":             ["RTSP", "HTTPS", "DNS", "NTP"],
    "printer":            ["IPP", "HTTP", "HTTPS", "DNS", "mDNS"],
    "router":             ["DHCP", "DNS", "NTP", "HTTPS"],
    "laptop":             ["HTTPS", "SSH", "DNS", "WebSocket", "TCP"],
    "smart_tv":           ["HTTPS", "QUIC", "UDP", "DNS"],
    "thermostat":         ["MQTT", "HTTPS", "DNS", "NTP"],
    "smart_door_lock":    ["MQTT", "HTTPS", "CoAP", "DNS"],
    "smart_light_hub":    ["Zigbee", "MQTT", "HTTPS", "DNS"],
    "temperature_sensor": ["CoAP", "MQTT", "DNS"],
    "network_gateway":    ["DHCP", "DNS", "NTP", "HTTPS", "MQTT"],
}

BYTE_RANGES = {
    "camera":             (30_000, 120_000, 500, 2_000),
    "printer":            (2_000, 10_000, 2_000, 15_000),
    "router":             (300, 800, 300, 800),
    "laptop":             (5_000, 50_000, 10_000, 100_000),
    "smart_tv":           (2_000, 8_000, 50_000, 500_000),
    "thermostat":         (200, 2_000, 200, 1_500),
    "smart_door_lock":    (100, 800, 100, 600),
    "smart_light_hub":    (300, 3_000, 200, 2_000),
    "temperature_sensor": (50, 500, 50, 300),
    "network_gateway":    (1_000, 5_000, 1_000, 5_000),
}


def generate_seed_devices() -> list[dict]:
    random.seed(42)
    devices = []
    for i, d in enumerate(DEVICE_FLEET):
        dtype = d["type"]
        tp = INITIAL_TRUST_PROFILES[d["name"]]
        trust = tp["trust"]
        status = "safe"
        if trust < 40:
            status = "compromised"
        elif trust < 70:
            status = "suspicious"

        devices.append({
            "device_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, d["name"])),
            "device_name": d["name"],
            "device_type": dtype,
            "ip_address": d["ip"],
            "mac_address": _mac(MAC_PREFIXES[dtype], i),
            "manufacturer": _pick(MANUFACTURERS[dtype]),
            "firmware_version": _pick(FIRMWARE[dtype]),
            "trust_score": trust,
            "risk_level": tp["risk"],
            "status": status,
        })
    return devices


def _name_to_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, name))


def generate_seed_topology() -> list[dict]:
    edges = []
    for src, tgt, conn_type in TOPOLOGY_EDGES:
        edges.append({
            "source_device": _name_to_uuid(src),
            "target_device": _name_to_uuid(tgt),
            "connection_type": conn_type,
        })
    return edges


def generate_seed_telemetry(num_per_device: int = 8) -> list[dict]:
    random.seed(42)
    rows = []
    now = datetime.now(timezone.utc)
    dest_pools = {
        "internal": ["192.168.1.1", "192.168.1.2", "192.168.1.10", "192.168.1.50", "192.168.1.100", "192.168.1.254"],
        "trusted_cloud": ["34.120.50.12", "52.94.236.248", "104.16.51.111", "142.250.80.46"],
        "external": ["45.33.32.156", "185.220.101.34", "91.219.236.222", "23.129.64.100"],
    }

    for d in DEVICE_FLEET:
        dtype = d["type"]
        dev_uuid = _name_to_uuid(d["name"])
        protocols = PROTOCOLS_BY_TYPE[dtype]
        bs_lo, bs_hi, br_lo, br_hi = BYTE_RANGES[dtype]

        for j in range(num_per_device):
            proto = random.choice(protocols)
            dest_type = random.choices(
                ["internal", "trusted_cloud", "external"],
                weights=[0.6, 0.35, 0.05],
                k=1,
            )[0]
            rows.append({
                "device_id": dev_uuid,
                "protocol": proto,
                "bytes_sent": random.randint(bs_lo, bs_hi),
                "bytes_received": random.randint(br_lo, br_hi),
                "packet_count": random.randint(5, 800),
                "session_duration": round(random.uniform(0.1, 30.0), 2),
                "destination_ip": random.choice(dest_pools[dest_type]),
                "destination_type": dest_type,
                "timestamp": (now - timedelta(minutes=random.randint(1, 120))).isoformat(),
            })
    return rows


def generate_seed_features() -> list[dict]:
    random.seed(42)
    rows = []
    for d in DEVICE_FLEET:
        dtype = d["type"]
        dev_uuid = _name_to_uuid(d["name"])
        bs_lo, bs_hi, br_lo, br_hi = BYTE_RANGES[dtype]
        avg_vol = (bs_lo + bs_hi) // 2 + (br_lo + br_hi) // 2
        rows.append({
            "device_id": dev_uuid,
            "packet_rate": round(random.uniform(0.5, 50.0), 2),
            "avg_session_duration": round(random.uniform(0.5, 30.0), 2),
            "traffic_volume": avg_vol + random.randint(-avg_vol // 4, avg_vol // 4),
            "destination_entropy": round(random.uniform(0.0, 2.5), 4),
            "protocol_entropy": round(random.uniform(0.0, 2.0), 4),
        })
    return rows


def generate_seed_alerts() -> list[dict]:
    rows = []
    for a in SAMPLE_ALERTS:
        rows.append({
            "device_id": _name_to_uuid(a["device"]),
            "alert_type": a["type"],
            "severity": a["severity"],
            "description": a["desc"],
            "confidence": random.uniform(0.6, 1.0),
            "resolved": False,
        })
    return rows


def generate_seed_trust_history() -> list[dict]:
    rows = []
    now = datetime.now(timezone.utc)
    for entry in TRUST_HISTORY_ENTRIES:
        dev_uuid = _name_to_uuid(entry["device"])
        for i, (score, reason) in enumerate(zip(entry["scores"], entry["reasons"])):
            rows.append({
                "device_id": dev_uuid,
                "trust_score": score,
                "reason": reason,
                "timestamp": (now - timedelta(hours=len(entry["scores"]) - i)).isoformat(),
            })
    return rows
