import random
from datetime import datetime, timezone
from typing import Optional

from app.services.ml_pipeline import pipeline


def compute_risk_level(score: int) -> str:
    if score >= 80:
        return "SAFE"
    elif score >= 60:
        return "LOW"
    elif score >= 40:
        return "MEDIUM"
    else:
        return "COMPROMISED"


def recover_trust_score(current: int) -> int:
    if current >= 90:
        return current
    delta = random.randint(1, 3)
    return min(100, current + delta)


def compute_ml_trust(device_id: str) -> Optional[dict]:
    return pipeline.get_device_trust_detail(device_id)


EVENT_PENALTIES: dict[str, tuple[int, int]] = {
    "TRAFFIC_SPIKE": (-20, -10),
    "POLICY_VIOLATION": (-30, -20),
    "NEW_DESTINATION": (-10, -5),
    "BACKDOOR": (-40, -25),
    "DATA_EXFILTRATION": (-25, -15),
}


def adjust_trust_score(current: int, event_type: str) -> int:
    if event_type not in EVENT_PENALTIES:
        return current
    low, high = EVENT_PENALTIES[event_type]
    delta = random.randint(low, high)
    return max(0, min(100, current + delta))


def apply_attack_penalty(current: int) -> int:
    delta = random.randint(-60, -40)
    return max(0, min(100, current + delta))


NORMAL_EVENT_TYPES = ["ROUTINE_SCAN", "HEARTBEAT", "CONFIG_SYNC", "TRAFFIC_FLUCTUATION"]


def generate_security_explanation(device: dict) -> str:
    risk = device.get("risk_level", "SAFE")
    score = device.get("trust_score", 100)
    rate = device.get("traffic_rate", 0.0)
    name = device.get("name", "Device")

    detail = pipeline.get_device_trust_detail(device.get("id", ""))
    signal_info = ""
    if detail:
        parts = []
        if detail["ml_anomaly_score"] > 0.3:
            parts.append(f"ML anomaly score {detail['ml_anomaly_score']:.2f} (penalty {detail['ml_penalty']:.1f})")
        if detail["drift_score"] > 0:
            parts.append(f"behavioral drift {detail['drift_score']:.2f} (penalty {detail['drift_penalty']:.1f})")
        if detail["drift_confirmed"]:
            parts.append("drift confirmed across multiple windows")
        if detail["policy_violations_total"] > 0:
            parts.append(f"{detail['policy_violations_total']} policy violations ({detail['policy_high_confidence']} high-confidence)")
        if parts:
            signal_info = " Signals: " + "; ".join(parts) + "."

    if risk == "SAFE":
        return (
            f"{name} is operating normally with a trust score of {score}/100. "
            f"Traffic rate is {rate:.1f} MB/s, within expected parameters. "
            f"No anomalies detected.{signal_info}"
        )
    elif risk == "LOW":
        return (
            f"{name} shows minor deviations with a trust score of {score}/100. "
            f"Current traffic rate is {rate:.1f} MB/s. "
            f"Monitor for further changes but no immediate action required.{signal_info}"
        )
    elif risk == "MEDIUM":
        return (
            f"{name} has a degraded trust score of {score}/100, indicating suspicious activity. "
            f"Traffic rate elevated at {rate:.1f} MB/s. "
            f"Recommend reviewing recent events and considering network isolation.{signal_info}"
        )
    else:
        return (
            f"CRITICAL: {name} has a trust score of {score}/100, signaling a likely compromise. "
            f"Traffic rate is {rate:.1f} MB/s — significantly above baseline. "
            f"Immediate isolation and forensic analysis strongly recommended.{signal_info}"
        )


_PORTS_BY_TYPE: dict[str, list[str]] = {
    "camera": ["554/RTSP", "80/HTTP", "443/HTTPS", "8080/HTTP-ALT"],
    "router": ["22/SSH", "80/HTTP", "443/HTTPS", "53/DNS", "161/SNMP"],
    "gateway": ["22/SSH", "80/HTTP", "443/HTTPS", "53/DNS", "8443/HTTPS-ALT"],
    "sensor": ["1883/MQTT", "8883/MQTTS", "5683/CoAP"],
    "smart_tv": ["80/HTTP", "443/HTTPS", "8008/Cast", "9197/DLNA"],
    "laptop": ["22/SSH", "443/HTTPS", "3389/RDP", "5900/VNC"],
    "smartphone": ["443/HTTPS", "5228/GCM", "80/HTTP"],
    "printer": ["9100/RAW", "631/IPP", "80/HTTP", "443/HTTPS"],
    "thermostat": ["1883/MQTT", "80/HTTP", "443/HTTPS"],
    "hub": ["80/HTTP", "443/HTTPS", "1883/MQTT", "5683/CoAP", "22/SSH"],
}
_DEFAULT_PORTS = ["80/HTTP", "443/HTTPS"]


def generate_open_ports(device_type: str) -> list[str]:
    return _PORTS_BY_TYPE.get(device_type.lower(), _DEFAULT_PORTS)


_PROTOCOLS_BY_TYPE: dict[str, dict[str, float]] = {
    "camera": {"RTSP": 65.0, "HTTP": 20.0, "HTTPS": 10.0, "Other": 5.0},
    "router": {"TCP": 40.0, "UDP": 30.0, "DNS": 15.0, "ICMP": 10.0, "Other": 5.0},
    "gateway": {"TCP": 45.0, "UDP": 25.0, "DNS": 15.0, "HTTPS": 10.0, "Other": 5.0},
    "sensor": {"MQTT": 70.0, "CoAP": 20.0, "HTTP": 5.0, "Other": 5.0},
    "smart_tv": {"HTTPS": 55.0, "HTTP": 25.0, "Cast": 15.0, "Other": 5.0},
    "laptop": {"HTTPS": 60.0, "HTTP": 15.0, "SSH": 10.0, "DNS": 10.0, "Other": 5.0},
    "smartphone": {"HTTPS": 70.0, "HTTP": 15.0, "GCM": 10.0, "Other": 5.0},
    "printer": {"RAW": 50.0, "IPP": 30.0, "HTTP": 15.0, "Other": 5.0},
    "thermostat": {"MQTT": 60.0, "HTTP": 25.0, "HTTPS": 10.0, "Other": 5.0},
    "hub": {"MQTT": 35.0, "HTTPS": 30.0, "CoAP": 20.0, "HTTP": 10.0, "Other": 5.0},
}
_DEFAULT_PROTOCOLS = {"HTTPS": 60.0, "HTTP": 30.0, "Other": 10.0}


def generate_protocol_usage(device_type: str) -> dict[str, float]:
    return _PROTOCOLS_BY_TYPE.get(device_type.lower(), _DEFAULT_PROTOCOLS)


_ALERT_TYPES = {"TRAFFIC_SPIKE", "POLICY_VIOLATION", "NEW_DESTINATION", "BACKDOOR", "DATA_EXFILTRATION"}


def should_create_alert(event_type: str, new_trust: int, old_trust: int) -> bool:
    if event_type in _ALERT_TYPES:
        return True
    return (old_trust - new_trust) > 15


_ALERT_MAP: dict[str, tuple[str, str, str]] = {
    "TRAFFIC_SPIKE": (
        "ANOMALOUS_TRAFFIC",
        "HIGH",
        "Abnormal traffic spike detected. Possible data exfiltration or DDoS participation.",
    ),
    "POLICY_VIOLATION": (
        "POLICY_VIOLATION",
        "CRITICAL",
        "Device violated security policy. Unauthorized access attempt or misconfiguration detected.",
    ),
    "NEW_DESTINATION": (
        "SUSPICIOUS_CONNECTION",
        "MEDIUM",
        "Device initiated connection to previously unseen destination. Possible C2 communication.",
    ),
    "BACKDOOR": (
        "BACKDOOR_DETECTED",
        "CRITICAL",
        "Backdoor implant detected — persistent remote access established. Lateral movement and persistent threat actor activity suspected.",
    ),
    "DATA_EXFILTRATION": (
        "DATA_EXFILTRATION",
        "HIGH",
        "Sustained data exfiltration stream detected — sensitive data may be leaving network via C2 channel.",
    ),
}
_DEFAULT_ALERT = (
    "TRUST_DEGRADATION",
    "MEDIUM",
    "Significant trust score drop detected. Device behavior has changed from baseline.",
)


def build_alert_payload(device: dict, event_type: str, new_trust: int) -> dict:
    alert_type, severity, message = _ALERT_MAP.get(event_type, _DEFAULT_ALERT)
    return {
        "device_id": device["id"],
        "device_name": device["name"],
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


SEED_DEVICES: list[dict] = [
    {
        "name": "Gateway-Primary",
        "device_type": "gateway",
        "ip_address": "192.168.1.1",
        "vendor": "Cisco",
        "trust_score": 95,
        "risk_level": "SAFE",
        "traffic_rate": 12.4,
        "status": "online",
    },
    {
        "name": "SecurityCam-Lobby",
        "device_type": "camera",
        "ip_address": "192.168.1.42",
        "vendor": "Hikvision",
        "trust_score": 90,
        "risk_level": "SAFE",
        "traffic_rate": 8.1,
        "status": "online",
    },
    {
        "name": "TempSensor-Floor2",
        "device_type": "sensor",
        "ip_address": "192.168.1.55",
        "vendor": "Texas Instruments",
        "trust_score": 88,
        "risk_level": "SAFE",
        "traffic_rate": 0.3,
        "status": "online",
    },
    {
        "name": "SmartTV-ConfRoom",
        "device_type": "smart_tv",
        "ip_address": "192.168.1.78",
        "vendor": "Samsung",
        "trust_score": 87,
        "risk_level": "SAFE",
        "traffic_rate": 5.7,
        "status": "online",
    },
    {
        "name": "Laptop-DevStation",
        "device_type": "laptop",
        "ip_address": "192.168.1.101",
        "vendor": "Dell",
        "trust_score": 92,
        "risk_level": "SAFE",
        "traffic_rate": 6.2,
        "status": "online",
    },
    {
        "name": "Printer-HQ",
        "device_type": "printer",
        "ip_address": "192.168.1.110",
        "vendor": "HP",
        "trust_score": 86,
        "risk_level": "SAFE",
        "traffic_rate": 2.9,
        "status": "online",
    },
    {
        "name": "Thermostat-Main",
        "device_type": "thermostat",
        "ip_address": "192.168.1.130",
        "vendor": "Nest",
        "trust_score": 91,
        "risk_level": "SAFE",
        "traffic_rate": 0.1,
        "status": "online",
    },
    {
        "name": "IoT-Hub-Central",
        "device_type": "hub",
        "ip_address": "192.168.1.150",
        "vendor": "SmartThings",
        "trust_score": 89,
        "risk_level": "SAFE",
        "traffic_rate": 4.5,
        "status": "online",
    },
    {
        "name": "SecurityCam-Parking",
        "device_type": "camera",
        "ip_address": "192.168.1.160",
        "vendor": "Dahua",
        "trust_score": 93,
        "risk_level": "SAFE",
        "traffic_rate": 7.2,
        "status": "online",
    },
    {
        "name": "Smartphone-Admin",
        "device_type": "smartphone",
        "ip_address": "192.168.1.200",
        "vendor": "Apple",
        "trust_score": 85,
        "risk_level": "SAFE",
        "traffic_rate": 3.8,
        "status": "online",
    },
]
