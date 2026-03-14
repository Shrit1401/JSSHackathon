from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from ..models import TelemetryRecord, DeviceState, DeviceType, Protocol, DestinationType
from ..device_profiles import DEVICE_PROFILES, DESTINATION_IP_POOLS, ATTACK_PROFILES


class TelemetryGenerator:
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.random = random.Random(seed)
        self.devices: list[DeviceState] = []
        self.telemetry_store: list[TelemetryRecord] = []
        self.window_counter = 0
        self._init_devices()

    def _init_devices(self):
        for device_type, profile in DEVICE_PROFILES.items():
            for i in range(profile["count"]):
                device = DeviceState(
                    device_id=f"{profile['id_prefix']}_{i + 1}",
                    device_type=device_type,
                    ip_address=profile["ip_range"].format(i=profile["ip_start"] + i),
                )
                self.devices.append(device)

    def _pick_protocol(self, profile: dict, attack: Optional[str] = None) -> Protocol:
        if attack and attack in ATTACK_PROFILES:
            return ATTACK_PROFILES[attack]["protocol_override"]
        protocols = list(profile["protocol_weights"].keys())
        weights = list(profile["protocol_weights"].values())
        return self.random.choices(protocols, weights=weights, k=1)[0]

    def _pick_destination(self, profile: dict, attack: Optional[str] = None) -> tuple[DestinationType, str]:
        if attack and attack in ATTACK_PROFILES:
            dest_type = ATTACK_PROFILES[attack]["destination_override"]
        else:
            dest_types = list(profile["destination_weights"].keys())
            dest_weights = list(profile["destination_weights"].values())
            dest_type = self.random.choices(dest_types, weights=dest_weights, k=1)[0]
        pool = DESTINATION_IP_POOLS[dest_type]
        dst_ip = self.random.choice(pool)
        return dest_type, dst_ip

    def _generate_traffic(self, profile: dict, attack: Optional[str] = None) -> dict:
        bs_min, bs_max = profile["bytes_sent"]
        br_min, br_max = profile["bytes_received"]
        sd_min, sd_max = profile["session_duration"]
        pc_min, pc_max = profile["packet_count"]

        bytes_sent = int(self.rng.uniform(bs_min, bs_max))
        bytes_received = int(self.rng.uniform(br_min, br_max))
        session_duration = round(float(self.rng.uniform(sd_min, sd_max)), 2)
        packet_count = int(self.rng.uniform(pc_min, pc_max))

        if attack and attack in ATTACK_PROFILES:
            atk = ATTACK_PROFILES[attack]
            bytes_sent = int(bytes_sent * atk["bytes_sent_multiplier"])
            bytes_received = int(bytes_received * atk["bytes_received_multiplier"])
            if "session_duration_override" in atk:
                sd_min_a, sd_max_a = atk["session_duration_override"]
                session_duration = round(float(self.rng.uniform(sd_min_a, sd_max_a)), 2)
            if "packet_count_multiplier" in atk:
                packet_count = int(packet_count * atk["packet_count_multiplier"])

        noise = float(self.rng.normal(0, 0.05))
        bytes_sent = max(0, int(bytes_sent * (1 + noise)))
        bytes_received = max(0, int(bytes_received * (1 + noise)))

        return {
            "bytes_sent": bytes_sent,
            "bytes_received": bytes_received,
            "session_duration": session_duration,
            "packet_count": packet_count,
        }

    def generate_record(self, device: DeviceState, base_time: datetime, attack: Optional[str] = None) -> TelemetryRecord:
        profile = DEVICE_PROFILES[device.device_type]
        protocol = self._pick_protocol(profile, attack)
        dest_type, dst_ip = self._pick_destination(profile, attack)
        traffic = self._generate_traffic(profile, attack)
        offset_seconds = float(self.rng.uniform(0, 10))
        timestamp = base_time + timedelta(seconds=offset_seconds)

        record = TelemetryRecord(
            record_id=str(uuid.uuid4()),
            device_id=device.device_id,
            device_type=device.device_type,
            src_ip=device.ip_address,
            dst_ip=dst_ip,
            protocol=protocol,
            bytes_sent=traffic["bytes_sent"],
            bytes_received=traffic["bytes_received"],
            session_duration=traffic["session_duration"],
            packet_count=traffic["packet_count"],
            destination_type=dest_type,
            timestamp=timestamp,
            window_id=self.window_counter,
        )
        device.last_seen = timestamp
        device.total_records += 1
        return record

    def generate_window(self, records_per_device: int = 3, attack_devices: Optional[dict[str, str]] = None) -> list[TelemetryRecord]:
        base_time = datetime.utcnow()
        self.window_counter += 1
        attack_devices = attack_devices or {}
        window_records = []

        for device in self.devices:
            attack = attack_devices.get(device.device_id)
            if attack:
                device.is_compromised = True
                device.active_attack = attack

            count = records_per_device
            if device.device_type == DeviceType.PRINTER:
                count = max(1, records_per_device // 2)
            elif device.device_type == DeviceType.ROUTER:
                count = records_per_device + 1

            for _ in range(count):
                record = self.generate_record(device, base_time, attack)
                window_records.append(record)

        self.telemetry_store.extend(window_records)
        return window_records

    def generate_baseline_windows(self, num_windows: int = 5, records_per_device: int = 3) -> list[TelemetryRecord]:
        all_records = []
        for _ in range(num_windows):
            records = self.generate_window(records_per_device=records_per_device)
            all_records.extend(records)
        return all_records

    def get_device_by_id(self, device_id: str) -> Optional[DeviceState]:
        for device in self.devices:
            if device.device_id == device_id:
                return device
        return None
