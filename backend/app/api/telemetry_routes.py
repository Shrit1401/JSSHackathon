from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.telemetry import DeviceType, TelemetrySummary
from app.services.telemetry_generator import TelemetryGenerator

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

generator = TelemetryGenerator(seed=42)
generator.generate_baseline_windows(num_windows=5, records_per_device=3)


@router.get("/records")
def get_telemetry(
    device_id: Optional[str] = None,
    device_type: Optional[DeviceType] = None,
    limit: int = Query(default=50, le=500),
):
    records = generator.get_all_telemetry()

    if device_id:
        records = [r for r in records if r.device_id == device_id]
    if device_type:
        records = [r for r in records if r.device_type == device_type]

    return records[-limit:]


@router.get("/records/latest")
def get_latest_window():
    return generator.get_latest_window()


@router.get("/summary")
def get_summary() -> TelemetrySummary:
    records = generator.get_all_telemetry()
    if not records:
        return TelemetrySummary(
            total_records=0,
            total_devices=len(generator.devices),
            records_by_device_type={},
            protocols_observed=[],
        )

    by_type: dict[str, int] = {}
    protocols_seen: set[str] = set()

    for r in records:
        by_type[r.device_type.value] = by_type.get(r.device_type.value, 0) + 1
        protocols_seen.add(r.protocol.value)

    return TelemetrySummary(
        total_records=len(records),
        total_devices=len(generator.devices),
        records_by_device_type=by_type,
        protocols_observed=sorted(protocols_seen),
        time_range_start=min(r.timestamp for r in records),
        time_range_end=max(r.timestamp for r in records),
    )


@router.get("/devices")
def get_devices(device_type: Optional[DeviceType] = None):
    if device_type:
        return generator.get_devices_by_type(device_type)
    return generator.devices


@router.get("/devices/{device_id}")
def get_device(device_id: str):
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return device


@router.get("/devices/{device_id}/records")
def get_device_telemetry(device_id: str, limit: int = Query(default=50, le=500)):
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return generator.get_telemetry_for_device(device_id)[-limit:]


@router.post("/generate")
def generate_new_window(
    records_per_device: int = Query(default=3, ge=1, le=10),
):
    records = generator.generate_window(records_per_device=records_per_device)
    return {"generated": len(records), "total": len(generator.get_all_telemetry()), "window_id": generator.window_counter}


@router.post("/simulate-attack")
def simulate_attack(device_id: str, attack_type: str):
    device = generator.get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")

    from app.config.device_profiles import ATTACK_PROFILES
    if attack_type not in ATTACK_PROFILES:
        raise HTTPException(status_code=400, detail=f"Unknown attack type '{attack_type}'. Available: {list(ATTACK_PROFILES.keys())}")

    attack_profile = ATTACK_PROFILES[attack_type]
    if device.device_type not in attack_profile["applicable_devices"]:
        raise HTTPException(
            status_code=400,
            detail=f"Attack '{attack_type}' not applicable to device type '{device.device_type.value}'",
        )

    records = generator.generate_window(
        records_per_device=3,
        attack_devices={device_id: attack_type},
    )

    attack_records = [r for r in records if r.device_id == device_id]
    return {
        "attack": attack_type,
        "device": device_id,
        "description": attack_profile["description"],
        "attack_records": attack_records,
        "total_window_records": len(records),
    }


@router.post("/reset")
def reset_telemetry():
    generator.reset()
    generator.generate_baseline_windows(num_windows=5, records_per_device=3)
    return {"status": "reset", "baseline_records": len(generator.get_all_telemetry())}
