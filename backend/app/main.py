from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.telemetry_routes import router as telemetry_router
from app.api.feature_routes import router as feature_router
from app.api.baseline_routes import router as baseline_router
from app.api.drift_routes import router as drift_router
from app.api.policy_routes import router as policy_router
from app.api.ml_routes import router as ml_router
from app.api.trust_routes import router as trust_router
from app.api.alert_routes import router as alert_router
from app.api.event_routes import router as event_router
from app.api.simulate_routes import router as simulate_router
from app.api.explain_routes import router as explain_router
from app.api.network_routes import router as network_router
from app.api.attack_routes import router as attack_router
from app.api.db_routes import router as db_router

app = FastAPI(
    title="IoT Sentinel — Network Telemetry Engine",
    description="Real-time IoT device telemetry ingestion, behavioral profiling, anomaly detection, and Supabase-backed persistence.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(telemetry_router)
app.include_router(feature_router)
app.include_router(baseline_router)
app.include_router(drift_router)
app.include_router(policy_router)
app.include_router(ml_router)
app.include_router(trust_router)
app.include_router(alert_router)
app.include_router(event_router)
app.include_router(simulate_router)
app.include_router(explain_router)
app.include_router(network_router)
app.include_router(attack_router)
app.include_router(db_router)


@app.get("/")
def root():
    return {
        "service": "IoT Sentinel",
        "version": "2.0.0",
        "status": "operational",
        "pipeline_stages": [
            "telemetry_ingestion",
            "feature_extraction",
            "baseline_modeling",
            "drift_detection",
            "policy_engine",
            "ml_anomaly_detection",
            "trust_scoring",
            "alert_generation",
        ],
        "new_endpoints": [
            "GET /network-map",
            "POST /simulate-attack",
            "POST /db/seed",
            "GET /db/devices",
            "GET /db/alerts",
        ],
        "database": "supabase",
        "device_types": [
            "camera", "printer", "router", "laptop", "smart_tv",
            "thermostat", "smart_door_lock", "smart_light_hub",
            "temperature_sensor", "network_gateway",
        ],
    }


@app.get("/health")
def health():
    return {"status": "healthy", "version": "2.0.0"}
