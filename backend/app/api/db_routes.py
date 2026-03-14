import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from typing import Optional

from app.database import service as db
from app.database.seed_data import (
    generate_seed_devices,
    generate_seed_topology,
    generate_seed_telemetry,
    generate_seed_features,
    generate_seed_alerts,
    generate_seed_trust_history,
)
from app.services import supabase_sync
from app.api.telemetry_routes import generator
from app.api.feature_routes import engine as feature_engine
from app.api.trust_routes import trust_engine
from app.api.alert_routes import alert_manager

router = APIRouter(prefix="/db", tags=["Supabase Database"])

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")


@router.get("/schema")
def get_schema():
    with open(SCHEMA_PATH, "r") as f:
        sql = f.read()
    return PlainTextResponse(content=sql, media_type="text/plain")


@router.post("/seed")
def seed_database():
    devices = generate_seed_devices()
    created_devices = []
    for d in devices:
        row = db.upsert_device(**d)
        created_devices.append(row)

    topo = generate_seed_topology()
    topo_count = 0
    for e in topo:
        db.upsert_topology(**e)
        topo_count += 1

    telemetry = generate_seed_telemetry(num_per_device=8)
    db.insert_telemetry_batch(telemetry)

    features = generate_seed_features()
    for f in features:
        db.insert_features(**f)

    trust_rows = generate_seed_trust_history()
    for t in trust_rows:
        db.insert_trust_history(**t)

    alert_rows = generate_seed_alerts()
    for a in alert_rows:
        db.insert_alert(**a)

    return {
        "seeded": True,
        "devices": len(created_devices),
        "topology_edges": topo_count,
        "telemetry_events": len(telemetry),
        "features": len(features),
        "trust_history_entries": len(trust_rows),
        "alerts": len(alert_rows),
    }


@router.post("/seed-from-pipeline")
def seed_from_pipeline():
    devices = supabase_sync.sync_devices(generator.devices)
    all_telemetry = generator.get_all_telemetry()
    telemetry_count = supabase_sync.sync_telemetry_batch(all_telemetry)
    all_features = feature_engine.get_latest_features()
    feature_count = supabase_sync.sync_features(all_features)
    all_trust = trust_engine.get_all_latest()
    trust_results = supabase_sync.sync_trust_scores(all_trust)
    alert_count = supabase_sync.sync_alerts_batch(alert_manager.alerts)

    return {
        "seeded": True,
        "source": "pipeline_state",
        "devices": len(devices),
        "telemetry_events": telemetry_count,
        "features": feature_count,
        "trust_scores_synced": len(trust_results),
        "alerts": alert_count,
    }


@router.get("/devices")
def list_db_devices():
    return db.get_all_devices()


@router.get("/devices/{device_id}")
def get_db_device(device_id: str):
    device = db.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in database")
    return device


@router.get("/devices/{device_id}/telemetry")
def get_db_telemetry(device_id: str, limit: int = Query(default=50, le=500)):
    return db.get_telemetry_for_device(device_id, limit=limit)


@router.get("/devices/{device_id}/features")
def get_db_features(device_id: str):
    feat = db.get_latest_features(device_id)
    if not feat:
        raise HTTPException(status_code=404, detail="No features found")
    return feat


@router.get("/devices/{device_id}/trust-history")
def get_db_trust_history(device_id: str, limit: int = Query(default=50, le=500)):
    return db.get_trust_history(device_id, limit=limit)


@router.get("/alerts")
def list_db_alerts(
    device_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=100, le=500),
):
    return db.get_alerts(device_id=device_id, severity=severity, limit=limit)


@router.post("/alerts/{alert_id}/resolve")
def resolve_db_alert(alert_id: str):
    result = db.resolve_alert(alert_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return result


@router.get("/topology")
def get_db_topology():
    return db.get_full_topology()


@router.get("/device-map")
def get_uuid_map():
    return supabase_sync.get_device_uuid_map()
