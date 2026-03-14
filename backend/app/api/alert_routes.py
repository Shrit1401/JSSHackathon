from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.alerts import Alert, AlertType, AlertSeverity, AlertSummary
from app.services.alert_manager import AlertManager
from app.api.drift_routes import drift_detector
from app.api.policy_routes import policy_engine
from app.api.ml_routes import ml_detector
from app.api.trust_routes import trust_engine

router = APIRouter(prefix="/alerts", tags=["Alert System"])

alert_manager = AlertManager(drift_detector, policy_engine, ml_detector, trust_engine)
alert_manager.scan_all()


@router.get("")
def get_alerts(
    alert_type: Optional[AlertType] = None,
    severity: Optional[AlertSeverity] = None,
    device_id: Optional[str] = None,
    limit: int = Query(default=100, le=500),
) -> list[Alert]:
    return alert_manager.get_alerts(alert_type, severity, device_id)[:limit]


@router.get("/critical")
def get_critical_alerts(limit: int = Query(default=50, le=200)) -> list[Alert]:
    high = alert_manager.get_alerts(severity=AlertSeverity.HIGH)
    critical = alert_manager.get_alerts(severity=AlertSeverity.CRITICAL)
    combined = sorted(critical + high, key=lambda a: a.timestamp, reverse=True)
    return combined[:limit]


@router.get("/device/{device_id}")
def get_device_alerts(device_id: str, limit: int = Query(default=50, le=200)) -> list[Alert]:
    return alert_manager.get_alerts(device_id=device_id)[:limit]


@router.post("/acknowledge/{alert_id}")
def acknowledge_alert(alert_id: str):
    if not alert_manager.acknowledge(alert_id):
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return {"alert_id": alert_id, "acknowledged": True}


@router.post("/refresh")
def refresh_alerts() -> AlertSummary:
    alert_manager.scan_all()
    return alert_manager.get_summary()


@router.get("/summary")
def get_alert_summary() -> AlertSummary:
    return alert_manager.get_summary()
