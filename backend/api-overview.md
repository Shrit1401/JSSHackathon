# IoT Sentinel — API Overview

**Base URL:** `http://localhost:8000`
**Version:** `2.0.0`
**Auth:** None (open CORS with `allow_origins=["*"]`)
**Total Endpoints:** 100 (68 GET, 32 POST)

---

## Table of Contents

1. [Root](#1-root)
2. [Telemetry](#2-telemetry)
3. [Feature Engineering](#3-feature-engineering)
4. [Baseline Learning](#4-baseline-learning)
5. [Drift Detection](#5-drift-detection)
6. [Policy Engine](#6-policy-engine)
7. [ML Anomaly Detection](#7-ml-anomaly-detection)
8. [Trust Scoring](#8-trust-scoring)
9. [Protection System](#9-protection-system)
10. [Alerts](#10-alerts)
11. [Event Timeline](#11-event-timeline)
12. [Attack Simulation](#12-attack-simulation)
13. [Attack Simulation v2 (Supabase-synced)](#13-attack-simulation-v2-supabase-synced)
14. [Explainability](#14-explainability)
15. [Network Map](#15-network-map)
16. [Database (Supabase)](#16-database-supabase)
17. [Enums Reference](#17-enums-reference)
18. [Models Reference](#18-models-reference)

---

## Pipeline Architecture

```
Telemetry → Features → Baselines → Drift Detection → Policy Engine → ML Scoring → Trust Scoring → Alerts
```

Every device goes through this 8-stage pipeline. Each stage has its own set of endpoints.

---

## 1. Root

### `GET /`

Returns service metadata including version, pipeline stages, and supported device types.

**Response:**

```json
{
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
    "alert_generation"
  ],
  "device_types": [
    "camera", "printer", "router", "laptop", "smart_tv",
    "thermostat", "smart_door_lock", "smart_light_hub",
    "temperature_sensor", "network_gateway"
  ],
  "database": "supabase"
}
```

---

### `GET /health`

Simple health check.

**Response:**

```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

---

## 2. Telemetry

Prefix: `/telemetry`

Handles raw network telemetry ingestion, device registry, and telemetry generation.

---

### `GET /telemetry/records`

Returns telemetry records with optional filtering.

| Parameter     | In    | Type                  | Required | Default | Constraints       |
|---------------|-------|-----------------------|----------|---------|-------------------|
| `device_id`   | query | `string`              | no       | —       |                   |
| `device_type` | query | `DeviceType` (enum)   | no       | —       |                   |
| `limit`       | query | `int`                 | no       | `50`    | max `500`         |

**Response:** `TelemetryRecord[]`

---

### `GET /telemetry/records/latest`

Returns telemetry records from the most recent generation window.

**Parameters:** None

**Response:** `TelemetryRecord[]`

---

### `GET /telemetry/summary`

Returns aggregate telemetry statistics.

**Parameters:** None

**Response:** `TelemetrySummary`

```json
{
  "total_records": 150,
  "total_devices": 10,
  "records_by_device_type": { "camera": 15, "router": 15 },
  "protocols_observed": ["HTTPS", "MQTT", "DNS"],
  "time_range_start": "2026-03-14T00:00:00Z",
  "time_range_end": "2026-03-14T12:00:00Z"
}
```

---

### `GET /telemetry/devices`

Lists all registered devices.

| Parameter     | In    | Type                | Required | Default |
|---------------|-------|---------------------|----------|---------|
| `device_type` | query | `DeviceType` (enum) | no       | —       |

**Response:** `DeviceState[]`

```json
[
  {
    "device_id": "camera-01",
    "device_type": "camera",
    "ip_address": "192.168.1.10",
    "is_compromised": false,
    "active_attack": null,
    "last_seen": "2026-03-14T12:00:00Z",
    "total_records": 30
  }
]
```

---

### `GET /telemetry/devices/{device_id}`

Returns a single device by ID.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** `DeviceState`

**Errors:** `404` if device not found.

---

### `GET /telemetry/devices/{device_id}/records`

Returns telemetry records for a specific device.

| Parameter   | In    | Type     | Required | Default | Constraints |
|-------------|-------|----------|----------|---------|-------------|
| `device_id` | path  | `string` | yes      | —       |             |
| `limit`     | query | `int`    | no       | `50`    | max `500`   |

**Response:** `TelemetryRecord[]`

---

### `POST /telemetry/generate`

Generates a new telemetry window for all devices. Each device produces `records_per_device` records.

| Parameter            | In    | Type  | Required | Default | Constraints   |
|----------------------|-------|-------|----------|---------|---------------|
| `records_per_device` | query | `int` | no       | `3`     | min `1`, max `10` |

**Response:**

```json
{
  "generated": 30,
  "total_records": 180,
  "window_id": 7
}
```

---

### `POST /telemetry/simulate-attack`

Generates one attack-tainted telemetry window for a specific device. Only that device's records are affected.

| Parameter     | In    | Type     | Required |
|---------------|-------|----------|----------|
| `device_id`   | query | `string` | yes      |
| `attack_type` | query | `string` | yes      |

**Response:**

```json
{
  "device_id": "camera-01",
  "attack_type": "data_exfiltration",
  "records_generated": 30,
  "window_id": 8,
  "records": [ ... ]
}
```

**Errors:** `404` if device not found. `400` if attack type unknown or not applicable to device type.

---

### `POST /telemetry/reset`

Resets all telemetry data and regenerates 5 baseline windows from scratch.

**Parameters:** None

**Response:**

```json
{
  "status": "reset_complete",
  "baseline_records": 150
}
```

---

## 3. Feature Engineering

Prefix: `/features`

Computes behavioral feature vectors from raw telemetry windows.

---

### `GET /features/latest`

Returns the most recent feature vector per device.

| Parameter     | In    | Type                | Required | Default |
|---------------|-------|---------------------|----------|---------|
| `device_type` | query | `DeviceType` (enum) | no       | —       |

**Response:** `DeviceFeatureVector[]`

```json
[
  {
    "device_id": "camera-01",
    "device_type": "camera",
    "window_id": 7,
    "packet_rate": 12.5,
    "avg_session_duration": 45.3,
    "total_bytes_sent": 102400,
    "total_bytes_received": 204800,
    "traffic_volume": 307200,
    "unique_destinations": 3,
    "destination_entropy": 1.58,
    "unique_protocols": 2,
    "protocol_entropy": 0.92,
    "protocol_distribution": { "HTTPS": 0.6, "RTSP": 0.4 },
    "external_connection_ratio": 0.33,
    "inbound_outbound_ratio": 2.0,
    "record_count": 3,
    "window_start": "2026-03-14T11:00:00Z",
    "window_end": "2026-03-14T12:00:00Z"
  }
]
```

---

### `GET /features/window/{window_id}`

Returns feature vectors for all devices in a specific telemetry window.

| Parameter   | In   | Type  | Required |
|-------------|------|-------|----------|
| `window_id` | path | `int` | yes      |

**Response:** `DeviceFeatureVector[]`

---

### `GET /features/device/{device_id}`

Returns all feature vectors ever computed for a device (across all windows).

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** `DeviceFeatureVector[]`

---

### `GET /features/device/{device_id}/timeline`

Returns the full feature timeline for a device.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** `DeviceFeatureTimeline`

```json
{
  "device_id": "camera-01",
  "device_type": "camera",
  "windows": [ ... ],
  "total_windows": 7
}
```

---

### `GET /features/summary`

Returns aggregate feature engineering statistics.

**Parameters:** None

**Response:** `FeatureSummary`

```json
{
  "total_devices": 10,
  "total_windows": 7,
  "features_computed": 70,
  "feature_names": [
    "packet_rate", "avg_session_duration", "traffic_volume",
    "total_bytes_sent", "total_bytes_received", "destination_entropy",
    "protocol_entropy", "unique_destinations", "unique_protocols",
    "external_connection_ratio", "inbound_outbound_ratio"
  ]
}
```

---

### `POST /features/recompute`

Deletes all existing features and recomputes them from all telemetry windows.

**Parameters:** None

**Response:**

```json
{
  "status": "recomputed",
  "features_generated": 70,
  "summary": { ... }
}
```

---

## 4. Baseline Learning

Prefix: `/baselines`

Manages learned behavioral baselines per device and per device type. Baselines are statistical profiles (mean, std, min, max, samples) across all feature dimensions.

---

### `GET /baselines/devices`

Returns all per-device baselines.

| Parameter     | In    | Type                | Required | Default |
|---------------|-------|---------------------|----------|---------|
| `device_type` | query | `DeviceType` (enum) | no       | —       |

**Response:** `DeviceBaseline[]`

---

### `GET /baselines/devices/{device_id}`

Returns the learned baseline for a specific device.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** `DeviceBaseline`

```json
{
  "device_id": "camera-01",
  "device_type": "camera",
  "is_frozen": false,
  "windows_learned": 5,
  "last_updated": "2026-03-14T12:00:00Z",
  "packet_rate": { "mean": 12.5, "std": 2.1, "min_val": 8.0, "max_val": 18.0, "samples": 5 },
  "avg_session_duration": { "mean": 45.0, "std": 5.0, "min_val": 35.0, "max_val": 55.0, "samples": 5 },
  "traffic_volume": { ... },
  "total_bytes_sent": { ... },
  "total_bytes_received": { ... },
  "destination_entropy": { ... },
  "protocol_entropy": { ... },
  "unique_destinations": { ... },
  "unique_protocols": { ... },
  "external_connection_ratio": { ... },
  "inbound_outbound_ratio": { ... },
  "allowed_protocols": ["HTTPS", "RTSP"],
  "expected_destination_types": ["INTERNAL", "TRUSTED_CLOUD"]
}
```

**Errors:** `404` if no baseline exists for the device.

---

### `GET /baselines/types`

Returns baselines aggregated per device type (across all devices of that type).

**Parameters:** None

**Response:** `DeviceTypeBaseline[]`

---

### `GET /baselines/types/{device_type}`

Returns the aggregate baseline for a specific device type.

| Parameter     | In   | Type                | Required |
|---------------|------|---------------------|----------|
| `device_type` | path | `DeviceType` (enum) | yes      |

**Response:** `DeviceTypeBaseline`

---

### `GET /baselines/deviation/{device_id}`

Computes z-score deviations from baseline for every feature window of a device.

| Parameter   | In    | Type     | Required | Default | Constraints          |
|-------------|-------|----------|----------|---------|----------------------|
| `device_id` | path  | `string` | yes      | —       |                      |
| `threshold` | query | `float`  | no       | `2.5`   | min `0.5`, max `10.0` |

**Response:** `BaselineDeviation[]`

```json
[
  {
    "device_id": "camera-01",
    "device_type": "camera",
    "window_id": 7,
    "deviations": {
      "packet_rate": 1.2,
      "traffic_volume": 3.8,
      "destination_entropy": 0.5
    },
    "max_deviation_feature": "traffic_volume",
    "max_deviation_zscore": 3.8,
    "features_beyond_threshold": ["traffic_volume"],
    "threshold_used": 2.5
  }
]
```

---

### `GET /baselines/deviation/{device_id}/latest`

Same as above but only for the most recent feature window.

| Parameter   | In    | Type     | Required | Default | Constraints          |
|-------------|-------|----------|----------|---------|----------------------|
| `device_id` | path  | `string` | yes      | —       |                      |
| `threshold` | query | `float`  | no       | `2.5`   | min `0.5`, max `10.0` |

**Response:** `BaselineDeviation`

---

### `POST /baselines/freeze/{device_id}`

Freezes a device's baseline so it won't be updated by new telemetry.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:**

```json
{
  "device_id": "camera-01",
  "is_frozen": true
}
```

---

### `POST /baselines/unfreeze/{device_id}`

Unfreezes a device's baseline to resume learning.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:**

```json
{
  "device_id": "camera-01",
  "is_frozen": false
}
```

---

### `POST /baselines/relearn`

Resets all baselines and re-learns from all current telemetry windows.

**Parameters:** None

**Response:**

```json
{
  "status": "relearned",
  ...
}
```

---

### `GET /baselines/summary`

Returns aggregate baseline statistics.

**Parameters:** None

**Response:** `BaselineSummary`

```json
{
  "total_device_baselines": 10,
  "total_type_baselines": 10,
  "frozen_devices": 0,
  "baseline_phase_windows": 5,
  "device_types_covered": ["camera", "router", "printer", ...]
}
```

---

## 5. Drift Detection

Prefix: `/drift`

Monitors behavioral drift from baselines using z-score analysis. Drift is confirmed after consecutive windows exceed thresholds.

---

### `GET /drift/status`

Returns current drift status for all devices.

| Parameter     | In    | Type                | Required | Default |
|---------------|-------|---------------------|----------|---------|
| `device_type` | query | `DeviceType` (enum) | no       | —       |

**Response:** `DeviceDriftState[]`

```json
[
  {
    "device_id": "camera-01",
    "device_type": "camera",
    "current_severity": "none",
    "is_drifting": false,
    "consecutive_drift_windows": 0,
    "max_consecutive_drift": 0,
    "total_drift_windows": 0,
    "total_windows_analyzed": 7,
    "latest_drift_score": 0.5,
    "peak_drift_score": 1.2,
    "currently_drifting_features": [],
    "historically_drifted_features": [],
    "first_drift_detected": null,
    "last_drift_detected": null,
    "drift_confirmed_at": null
  }
]
```

---

### `GET /drift/status/{device_id}`

Returns drift status for a specific device.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** `DeviceDriftState`

**Errors:** `404` if device not found.

---

### `GET /drift/drifting`

Returns only devices currently flagged as drifting.

**Parameters:** None

**Response:** `DeviceDriftState[]`

---

### `GET /drift/history/{device_id}`

Returns the full drift analysis history for a device.

| Parameter   | In    | Type     | Required | Default | Constraints |
|-------------|-------|----------|----------|---------|-------------|
| `device_id` | path  | `string` | yes      | —       |             |
| `limit`     | query | `int`    | no       | `50`    | max `200`   |

**Response:** `DriftResult[]`

```json
[
  {
    "device_id": "camera-01",
    "device_type": "camera",
    "window_id": 7,
    "timestamp": "2026-03-14T12:00:00Z",
    "is_drifting": true,
    "severity": "medium",
    "drift_score": 4.2,
    "consecutive_drift_windows": 2,
    "drifting_features": [
      {
        "feature_name": "traffic_volume",
        "z_score": 4.2,
        "abs_z_score": 4.2,
        "baseline_mean": 102400,
        "baseline_std": 20000,
        "current_value": 186400,
        "is_drifting": true,
        "consecutive_windows": 2
      }
    ],
    "top_drifting_feature": "traffic_volume",
    "top_z_score": 4.2,
    "total_features_checked": 11,
    "features_beyond_threshold": 1
  }
]
```

---

### `GET /drift/history/{device_id}/latest`

Returns the most recent drift result for a device.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** `DriftResult`

---

### `GET /drift/events`

Returns drift events (state transitions like drift_started, drift_confirmed, drift_resolved).

| Parameter    | In    | Type     | Required | Default | Constraints |
|--------------|-------|----------|----------|---------|-------------|
| `device_id`  | query | `string` | no       | —       |             |
| `event_type` | query | `string` | no       | —       |             |
| `limit`      | query | `int`    | no       | `50`    | max `200`   |

**Response:** `DriftEvent[]`

---

### `POST /drift/analyze-latest`

Runs drift analysis on the most recent feature window for all devices.

**Parameters:** None

**Response:** `DriftResult[]`

---

### `GET /drift/summary`

Returns aggregate drift statistics.

**Parameters:** None

**Response:** `DriftSummary`

```json
{
  "total_devices_monitored": 10,
  "devices_currently_drifting": 1,
  "devices_by_severity": { "none": 9, "medium": 1 },
  "total_drift_events": 3,
  "confirmation_windows": 3,
  "z_score_threshold": 2.5
}
```

---

## 6. Policy Engine

Prefix: `/policies`

Evaluates telemetry records against configurable policy rules (protocol blacklists, traffic ceilings, destination restrictions, etc.).

---

### `GET /policies/rules`

Returns all configured policy rules.

| Parameter     | In    | Type                | Required | Default |
|---------------|-------|---------------------|----------|---------|
| `device_type` | query | `DeviceType` (enum) | no       | —       |

**Response:** `PolicyRule[]`

```json
[
  {
    "rule_id": "rule-001",
    "policy_type": "protocol_blacklist",
    "device_type": "camera",
    "description": "Cameras must not use TELNET or FTP",
    "confidence": "high",
    "parameters": { "blocked_protocols": ["TELNET", "FTP"] }
  }
]
```

---

### `GET /policies/violations`

Returns policy violations with optional filtering.

| Parameter     | In    | Type                  | Required | Default | Constraints |
|---------------|-------|-----------------------|----------|---------|-------------|
| `device_id`   | query | `string`              | no       | —       |             |
| `policy_type` | query | `PolicyType` (enum)   | no       | —       |             |
| `confidence`  | query | `Confidence` (enum)   | no       | —       |             |
| `limit`       | query | `int`                 | no       | `50`    | max `500`   |

**Response:** `PolicyViolation[]`

```json
[
  {
    "violation_id": "viol-001",
    "rule_id": "rule-001",
    "policy_type": "protocol_blacklist",
    "device_id": "camera-01",
    "device_type": "camera",
    "confidence": "high",
    "description": "Camera used blocked protocol TELNET",
    "evidence": { "protocol": "TELNET", "record_id": "rec-123" },
    "record_id": "rec-123",
    "timestamp": "2026-03-14T12:00:00Z"
  }
]
```

---

### `GET /policies/violations/high-confidence`

Returns only high-confidence policy violations.

| Parameter | In    | Type  | Required | Default | Constraints |
|-----------|-------|-------|----------|---------|-------------|
| `limit`   | query | `int` | no       | `50`    | max `500`   |

**Response:** `PolicyViolation[]`

---

### `GET /policies/devices`

Returns compliance state for all devices.

| Parameter     | In    | Type                | Required | Default |
|---------------|-------|---------------------|----------|---------|
| `device_type` | query | `DeviceType` (enum) | no       | —       |

**Response:** `DevicePolicyState[]`

```json
[
  {
    "device_id": "camera-01",
    "device_type": "camera",
    "total_records_evaluated": 30,
    "total_violations": 2,
    "violations_by_type": { "protocol_blacklist": 2 },
    "violation_rate": 0.067,
    "last_violation": "2026-03-14T12:00:00Z",
    "is_compliant": false
  }
]
```

---

### `GET /policies/devices/{device_id}`

Returns compliance state for a specific device.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** `DevicePolicyState`

**Errors:** `404` if device not found.

---

### `GET /policies/devices/{device_id}/violations`

Returns policy violations for a specific device.

| Parameter   | In    | Type     | Required | Default | Constraints |
|-------------|-------|----------|----------|---------|-------------|
| `device_id` | path  | `string` | yes      | —       |             |
| `limit`     | query | `int`    | no       | `50`    | max `500`   |

**Response:** `PolicyViolation[]`

---

### `GET /policies/non-compliant`

Returns devices currently non-compliant with policies.

**Parameters:** None

**Response:** `DevicePolicyState[]`

---

### `POST /policies/evaluate-latest`

Evaluates the latest telemetry window against all policy rules.

**Parameters:** None

**Response:**

```json
{
  "records_evaluated": 30,
  "records_with_violations": 2,
  "new_violations": 3
}
```

---

### `POST /policies/recheck`

Resets all policy state and re-evaluates all telemetry from scratch.

**Parameters:** None

**Response:**

```json
{
  "records_evaluated": 180,
  "records_with_violations": 5,
  "total_violations": 8
}
```

---

### `GET /policies/summary`

Returns aggregate policy engine statistics.

**Parameters:** None

**Response:** `PolicySummary`

```json
{
  "total_rules": 25,
  "rules_by_type": { "protocol_blacklist": 10, "traffic_ceiling": 5, ... },
  "rules_by_device_type": { "camera": 5, "router": 3, ... },
  "total_violations": 8,
  "devices_with_violations": 2,
  "total_records_evaluated": 180
}
```

---

## 7. ML Anomaly Detection

Prefix: `/ml`

Isolation Forest-based anomaly detection that scores device feature vectors.

---

### `GET /ml/scores/latest`

Returns the latest ML anomaly score per device.

| Parameter     | In    | Type                | Required | Default |
|---------------|-------|---------------------|----------|---------|
| `device_type` | query | `DeviceType` (enum) | no       | —       |

**Response:** `AnomalyScore[]`

```json
[
  {
    "device_id": "camera-01",
    "device_type": "camera",
    "window_id": 7,
    "anomaly_score": 0.35,
    "raw_score": -0.15,
    "is_anomalous": false,
    "threshold": 0.5,
    "feature_contributions": {
      "packet_rate": 0.05,
      "traffic_volume": 0.12,
      "destination_entropy": 0.08,
      ...
    },
    "timestamp": "2026-03-14T12:00:00Z"
  }
]
```

---

### `GET /ml/scores/{device_id}`

Returns historical anomaly scores for a device.

| Parameter   | In    | Type     | Required | Default | Constraints |
|-------------|-------|----------|----------|---------|-------------|
| `device_id` | path  | `string` | yes      | —       |             |
| `limit`     | query | `int`    | no       | `50`    | max `200`   |

**Response:** `AnomalyScore[]`

---

### `GET /ml/scores/{device_id}/latest`

Returns the single most recent anomaly score for a device.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** `AnomalyScore`

---

### `GET /ml/anomalous`

Returns devices currently flagged as anomalous by the ML model.

**Parameters:** None

**Response:** `AnomalyScore[]`

---

### `POST /ml/score-latest`

Runs the ML model on the most recent feature window and returns scores for all devices.

**Parameters:** None

**Response:** `AnomalyScore[]`

---

### `GET /ml/model`

Returns metadata about the loaded ML model.

**Parameters:** None

**Response:** `MLModelInfo`

```json
{
  "model_type": "IsolationForest",
  "training_samples": 50,
  "training_features": [
    "packet_rate", "avg_session_duration", "traffic_volume",
    "total_bytes_sent", "total_bytes_received", "destination_entropy",
    "protocol_entropy", "unique_destinations", "unique_protocols",
    "external_connection_ratio", "inbound_outbound_ratio"
  ],
  "contamination": 0.1,
  "trained_at": "2026-03-14T10:00:00Z",
  "dataset_source": "baseline_windows",
  "benign_samples": 45,
  "malicious_samples": 5
}
```

---

### `GET /ml/summary`

Returns aggregate ML detection statistics.

**Parameters:** None

**Response:** `MLSummary`

```json
{
  "model_loaded": true,
  "model_info": { ... },
  "total_scored": 70,
  "anomalies_detected": 3,
  "anomaly_rate": 0.043
}
```

---

## 8. Trust Scoring

Prefix: `/trust`

Computes composite trust scores (0–100) from ML anomaly, drift, and policy signals. Determines risk levels and controls baseline update gating.

---

### `GET /trust/scores`

Returns trust scores for all devices.

| Parameter     | In    | Type                | Required | Default |
|---------------|-------|---------------------|----------|---------|
| `device_type` | query | `DeviceType` (enum) | no       | —       |
| `risk_level`  | query | `RiskLevel` (enum)  | no       | —       |

**Response:** `DeviceTrustScore[]`

```json
[
  {
    "device_id": "camera-01",
    "device_type": "camera",
    "trust_score": 85.2,
    "risk_level": "LOW",
    "signal_breakdown": {
      "ml_anomaly_score": 0.35,
      "ml_penalty": 5.0,
      "drift_score": 1.2,
      "drift_normalized": 0.12,
      "drift_penalty": 3.0,
      "drift_confirmed": false,
      "drift_confirmation_penalty": 0.0,
      "policy_violations_total": 1,
      "policy_high_confidence": 0,
      "policy_penalty": 2.0,
      "total_penalty": 10.0
    },
    "baseline_update_allowed": true,
    "timestamp": "2026-03-14T12:00:00Z"
  }
]
```

---

### `GET /trust/scores/{device_id}`

Returns the current trust score for a specific device.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** `DeviceTrustScore`

**Errors:** `404` if device not found.

---

### `GET /trust/scores/{device_id}/history`

Returns full trust score history for a device.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** `DeviceTrustHistory`

```json
{
  "device_id": "camera-01",
  "device_type": "camera",
  "scores": [ ... ],
  "current_score": 85.2,
  "current_risk": "LOW",
  "lowest_score": 42.0,
  "highest_score": 98.5,
  "average_score": 78.3
}
```

---

### `GET /trust/at-risk`

Returns devices with HIGH or MEDIUM risk levels.

**Parameters:** None

**Response:** `DeviceTrustScore[]`

---

### `POST /trust/recompute`

Re-ingests latest features and recomputes trust scores for all devices.

**Parameters:** None

**Response:** `DeviceTrustScore[]`

---

### `GET /trust/summary`

Returns aggregate trust scoring statistics.

**Parameters:** None

**Response:** `TrustSummary`

```json
{
  "total_devices": 10,
  "devices_by_risk": { "SAFE": 7, "LOW": 2, "MEDIUM": 1 },
  "average_trust": 82.5,
  "lowest_trust_device": "camera-01",
  "lowest_trust_score": 42.0,
  "baseline_updates_blocked": 1,
  "weights": { "ml": 0.4, "drift": 0.35, "policy": 0.25 }
}
```

---

## 9. Protection System

Prefix: `/trust/protection`

Manages baseline update gating, device quarantine, and poisoning detection. Part of the trust module.

---

### `GET /trust/protection/status`

Returns protection state for all devices.

**Parameters:** None

**Response:** `DeviceProtectionState[]`

```json
[
  {
    "device_id": "camera-01",
    "device_type": "camera",
    "status": "learning",
    "is_frozen": false,
    "is_quarantined": false,
    "trust_score": 85.2,
    "consecutive_denied": 0,
    "total_allowed": 5,
    "total_denied": 0,
    "poisoning_attempts": 0,
    "baseline_integrity": 1.0,
    "last_allowed_update": "2026-03-14T12:00:00Z",
    "last_decision": "allowed",
    "last_decision_time": "2026-03-14T12:00:00Z"
  }
]
```

---

### `GET /trust/protection/status/{device_id}`

Returns protection state for a specific device.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** `DeviceProtectionState`

---

### `GET /trust/protection/quarantined`

Returns all currently quarantined devices.

**Parameters:** None

**Response:** `DeviceProtectionState[]`

---

### `POST /trust/protection/lift-quarantine/{device_id}`

Manually lifts quarantine on a device, restoring it to learning state.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:**

```json
{
  "device_id": "camera-01",
  "quarantine_lifted": true,
  "status": "learning"
}
```

---

### `GET /trust/protection/gate-log`

Returns baseline update gate events (accept/reject decisions).

| Parameter   | In    | Type                    | Required | Default | Constraints |
|-------------|-------|-------------------------|----------|---------|-------------|
| `device_id` | query | `string`                | no       | —       |             |
| `decision`  | query | `GateDecision` (enum)   | no       | —       |             |
| `limit`     | query | `int`                   | no       | `100`   | max `500`   |

**Response:** `GateEvent[]`

```json
[
  {
    "device_id": "camera-01",
    "device_type": "camera",
    "decision": "allowed",
    "trust_score": 85.2,
    "threshold": 60.0,
    "reason": "Trust score above threshold",
    "timestamp": "2026-03-14T12:00:00Z"
  }
]
```

---

### `GET /trust/protection/poisoning-attempts`

Returns detected baseline poisoning attempts.

| Parameter   | In    | Type     | Required | Default | Constraints |
|-------------|-------|----------|----------|---------|-------------|
| `device_id` | query | `string` | no       | —       |             |
| `limit`     | query | `int`    | no       | `50`    | max `200`   |

**Response:** `PoisoningAttempt[]`

```json
[
  {
    "device_id": "camera-01",
    "device_type": "camera",
    "trust_score_at_time": 35.0,
    "protection_status": "quarantined",
    "feature_drift_detected": true,
    "reason": "Baseline update denied due to low trust + active drift",
    "timestamp": "2026-03-14T12:05:00Z"
  }
]
```

---

### `GET /trust/protection/summary`

Returns aggregate protection system statistics.

**Parameters:** None

**Response:** `ProtectionSummary`

```json
{
  "total_devices": 10,
  "devices_learning": 8,
  "devices_frozen": 1,
  "devices_quarantined": 1,
  "total_gate_events": 50,
  "total_allowed": 45,
  "total_denied": 5,
  "total_poisoning_attempts": 2,
  "average_integrity": 0.95,
  "quarantine_threshold": 3,
  "trust_gate_threshold": 60.0
}
```

---

## 10. Alerts

Prefix: `/alerts`

Aggregates alerts from all detection engines (drift, policy, ML, trust, protection).

---

### `GET /alerts`

Returns all alerts with optional filtering.

| Parameter    | In    | Type                      | Required | Default | Constraints |
|--------------|-------|---------------------------|----------|---------|-------------|
| `alert_type` | query | `AlertType` (enum)        | no       | —       |             |
| `severity`   | query | `AlertSeverity` (enum)    | no       | —       |             |
| `device_id`  | query | `string`                  | no       | —       |             |
| `limit`      | query | `int`                     | no       | `100`   | max `500`   |

**Response:** `Alert[]`

```json
[
  {
    "alert_id": "alert-001",
    "alert_type": "DRIFT_CONFIRMED",
    "severity": "HIGH",
    "device_id": "camera-01",
    "device_type": "camera",
    "title": "Drift Confirmed on camera-01",
    "reason": "Behavioral drift confirmed over 3 consecutive windows",
    "evidence": {
      "drift_score": 4.2,
      "consecutive_windows": 3,
      "drifting_features": ["traffic_volume", "destination_entropy"]
    },
    "trust_score_at_time": 42.0,
    "timestamp": "2026-03-14T12:00:00Z",
    "acknowledged": false
  }
]
```

---

### `GET /alerts/critical`

Returns only HIGH and CRITICAL severity alerts.

| Parameter | In    | Type  | Required | Default | Constraints |
|-----------|-------|-------|----------|---------|-------------|
| `limit`   | query | `int` | no       | `50`    | max `200`   |

**Response:** `Alert[]`

---

### `GET /alerts/device/{device_id}`

Returns all alerts for a specific device.

| Parameter   | In    | Type     | Required | Default | Constraints |
|-------------|-------|----------|----------|---------|-------------|
| `device_id` | path  | `string` | yes      | —       |             |
| `limit`     | query | `int`    | no       | `50`    | max `200`   |

**Response:** `Alert[]`

---

### `POST /alerts/acknowledge/{alert_id}`

Acknowledges a specific alert.

| Parameter  | In   | Type     | Required |
|------------|------|----------|----------|
| `alert_id` | path | `string` | yes      |

**Response:**

```json
{
  "alert_id": "alert-001",
  "acknowledged": true
}
```

**Errors:** `404` if alert not found.

---

### `POST /alerts/refresh`

Re-scans all detection engines and regenerates the full alert set.

**Parameters:** None

**Response:** `AlertSummary`

---

### `GET /alerts/summary`

Returns aggregate alert statistics.

**Parameters:** None

**Response:** `AlertSummary`

```json
{
  "total_alerts": 5,
  "by_type": { "DRIFT_CONFIRMED": 1, "POLICY_VIOLATION": 2, "ML_ANOMALY": 2 },
  "by_severity": { "HIGH": 1, "MEDIUM": 2, "LOW": 2 },
  "by_device": { "camera-01": 3, "router-01": 2 },
  "unacknowledged": 4,
  "most_recent": "2026-03-14T12:00:00Z"
}
```

---

## 11. Event Timeline

Prefix: `/events`

Unified timeline of all system events across all pipeline stages.

---

### `GET /events`

Returns all timeline events with optional filtering.

| Parameter    | In    | Type                      | Required | Default | Constraints |
|--------------|-------|---------------------------|----------|---------|-------------|
| `category`   | query | `EventCategory` (enum)    | no       | —       |             |
| `device_id`  | query | `string`                  | no       | —       |             |
| `event_type` | query | `string`                  | no       | —       |             |
| `limit`      | query | `int`                     | no       | `100`   | max `500`   |

**Response:** `Event[]`

```json
[
  {
    "event_id": "evt-001",
    "category": "ATTACK",
    "event_type": "attack_started",
    "device_id": "camera-01",
    "device_type": "camera",
    "description": "Simulating data_exfiltration on camera-01 for 3 cycles",
    "metadata": { "attack_type": "data_exfiltration", "cycles": 3 },
    "timestamp": "2026-03-14T12:00:00Z"
  }
]
```

---

### `GET /events/device/{device_id}`

Returns timeline events for a specific device.

| Parameter   | In    | Type     | Required | Default | Constraints |
|-------------|-------|----------|----------|---------|-------------|
| `device_id` | path  | `string` | yes      | —       |             |
| `limit`     | query | `int`    | no       | `100`   | max `500`   |

**Response:** `Event[]`

---

### `GET /events/attacks`

Returns events in the ATTACK category.

| Parameter | In    | Type  | Required | Default | Constraints |
|-----------|-------|-------|----------|---------|-------------|
| `limit`   | query | `int` | no       | `50`    | max `200`   |

**Response:** `Event[]`

---

### `GET /events/detections`

Returns events in the DETECTION category.

| Parameter | In    | Type  | Required | Default | Constraints |
|-----------|-------|-------|----------|---------|-------------|
| `limit`   | query | `int` | no       | `50`    | max `200`   |

**Response:** `Event[]`

---

### `GET /events/summary`

Returns aggregate event statistics.

**Parameters:** None

**Response:** `EventSummary`

```json
{
  "total_events": 25,
  "by_category": { "ATTACK": 5, "DETECTION": 10, "SYSTEM": 10 },
  "by_device": { "camera-01": 8, "router-01": 5 },
  "earliest": "2026-03-14T10:00:00Z",
  "latest": "2026-03-14T12:00:00Z"
}
```

---

## 12. Attack Simulation

Prefix: `/simulate`

Runs end-to-end attack simulations through the full pipeline (telemetry → features → drift → policy → ML → trust → alerts). Does NOT sync to Supabase.

---

### `GET /simulate/attacks`

Lists all available attack types with descriptions and applicable device types.

**Parameters:** None

**Response:**

```json
{
  "data_exfiltration": {
    "description": "Simulates large outbound data transfers to external destinations",
    "applicable_devices": ["camera", "laptop", "router"]
  },
  "port_scanning": {
    "description": "Simulates network reconnaissance via port scanning",
    "applicable_devices": ["laptop", "router"]
  },
  ...
}
```

---

### `POST /simulate/attack`

Runs a full-pipeline attack simulation on a single device for N cycles.

| Parameter     | In    | Type     | Required | Default | Constraints       |
|---------------|-------|----------|----------|---------|-------------------|
| `device_id`   | query | `string` | yes      | —       |                   |
| `attack_type` | query | `string` | yes      | —       |                   |
| `cycles`      | query | `int`    | no       | `1`     | min `1`, max `10` |

**Response:**

```json
{
  "attack": "data_exfiltration",
  "description": "Simulates large outbound data transfers to external destinations",
  "device": "camera-01",
  "cycles_run": 3,
  "cycle_results": [
    {
      "cycle": 1,
      "trust_score": 78.5,
      "risk_level": "LOW",
      "drift_score": 2.1,
      "is_drifting": false,
      "drift_severity": "none"
    },
    {
      "cycle": 2,
      "trust_score": 55.2,
      "risk_level": "MEDIUM",
      "drift_score": 4.8,
      "is_drifting": true,
      "drift_severity": "medium"
    },
    {
      "cycle": 3,
      "trust_score": 32.0,
      "risk_level": "HIGH",
      "drift_score": 7.2,
      "is_drifting": true,
      "drift_severity": "high"
    }
  ],
  "final_state": {
    "trust_score": 32.0,
    "risk_level": "HIGH",
    "baseline_frozen": true,
    "quarantined": true,
    "poisoning_attempts": 2
  },
  "total_alerts": 5
}
```

**Errors:** `404` if device not found. `400` if attack type unknown or not applicable.

---

### `POST /simulate/multi-attack`

Runs simultaneous attacks on multiple devices through the full pipeline.

| Parameter | In    | Type  | Required | Default | Constraints       |
|-----------|-------|-------|----------|---------|-------------------|
| `cycles`  | query | `int` | no       | `3`     | min `1`, max `10` |

**Request Body:**

```json
{
  "camera-01": "data_exfiltration",
  "router-01": "port_scanning"
}
```

Body is a `dict[str, str]` mapping `device_id → attack_type`.

**Response:**

```json
{
  "attacks": { "camera-01": "data_exfiltration", "router-01": "port_scanning" },
  "cycles_run": 3,
  "device_results": {
    "camera-01": {
      "trust_score": 32.0,
      "risk_level": "HIGH",
      "quarantined": true
    },
    "router-01": {
      "trust_score": 45.0,
      "risk_level": "MEDIUM",
      "quarantined": false
    }
  },
  "total_alerts": 8
}
```

**Errors:** `404` if any device not found. `400` if any attack type unknown.

---

## 13. Attack Simulation v2 (Supabase-synced)

No prefix (mounted at root).

Enhanced attack simulation that runs the full pipeline AND syncs results (telemetry, features, trust scores, alerts) to Supabase.

---

### `POST /simulate-attack`

Runs a full-pipeline attack simulation with Supabase sync.

**Request Body:** `AttackRequest`

```json
{
  "device_id": "camera-01",
  "attack_type": "data_exfiltration",
  "cycles": 3
}
```

| Body Field    | Type     | Required | Default |
|---------------|----------|----------|---------|
| `device_id`   | `string` | yes      | —       |
| `attack_type` | `string` | yes      | —       |
| `cycles`      | `int`    | no       | `3`     |

**Response:** Same shape as `POST /simulate/attack` with an additional field:

```json
{
  "attack": "data_exfiltration",
  "description": "...",
  "device": "camera-01",
  "cycles_run": 3,
  "cycle_results": [ ... ],
  "final_state": { ... },
  "total_alerts": 5,
  "synced_to_supabase": true
}
```

**Errors:** `404` if device not found. `400` if attack type unknown or not applicable.

---

### `GET /simulate-attack/types`

Lists all available attack types (same as `GET /simulate/attacks`).

**Parameters:** None

**Response:**

```json
{
  "data_exfiltration": {
    "description": "...",
    "applicable_devices": ["camera", "laptop", "router"]
  },
  ...
}
```

---

## 14. Explainability

Prefix: `/devices`

Provides human-readable explanations for why a device was flagged, combining signals from drift, policy, ML, trust, and baseline engines.

---

### `GET /devices/{device_id}/explain`

Returns a full explainability report for a device.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:**

```json
{
  "device_id": "camera-01",
  "device_type": "camera",
  "is_flagged": true,
  "trust_score": 32.0,
  "risk_level": "HIGH",
  "signal_breakdown": { ... },
  "drift_analysis": {
    "is_drifting": true,
    "severity": "high",
    "drift_score": 7.2,
    "drifting_features": ["traffic_volume", "destination_entropy"]
  },
  "policy_analysis": {
    "is_compliant": false,
    "total_violations": 3,
    "violations": [ ... ]
  },
  "ml_analysis": {
    "is_anomalous": true,
    "anomaly_score": 0.82,
    "top_features": { ... }
  },
  "baseline_analysis": {
    "is_frozen": true,
    "windows_learned": 5,
    "max_deviation": 7.2
  },
  "protection_state": {
    "status": "quarantined",
    "is_quarantined": true,
    "poisoning_attempts": 2
  },
  "reasons": [
    "High behavioral drift detected (score: 7.2)",
    "ML model flags device as anomalous (score: 0.82)",
    "3 policy violations detected",
    "Device quarantined after 2 poisoning attempts"
  ]
}
```

---

### `GET /devices/{device_id}/explain/summary`

Returns a condensed explainability summary.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:**

```json
{
  "device_id": "camera-01",
  "is_flagged": true,
  "trust_score": 32.0,
  "risk_level": "HIGH",
  "reasons": [
    "High behavioral drift detected",
    "ML anomaly flagged",
    "Policy violations found",
    "Device quarantined"
  ],
  "summary": "camera-01 is flagged HIGH risk due to confirmed behavioral drift, ML anomaly detection, and policy violations."
}
```

---

## 15. Network Map

Prefix: `/network-map`

Returns network topology as flat node/edge lists and hierarchical tree structures. Falls back to in-memory data if Supabase is empty.

---

### `GET /network-map`

Returns the full network topology: nodes, edges, and tree.

**Parameters:** None

**Response:**

```json
{
  "nodes": [
    {
      "id": "camera-01",
      "type": "camera",
      "ip": "192.168.1.10",
      "parent": "router-01",
      ...
    }
  ],
  "edges": [
    {
      "source": "router-01",
      "target": "camera-01",
      "type": "wired",
      ...
    }
  ],
  "tree": [
    {
      "id": "network_gateway-01",
      "children": [
        {
          "id": "router-01",
          "children": [
            { "id": "camera-01", "children": [] }
          ]
        }
      ]
    }
  ],
  "total_nodes": 10,
  "total_edges": 9,
  "source": "supabase"
}
```

---

### `GET /network-map/flat`

Returns just the flat node and edge lists (no tree).

**Parameters:** None

**Response:**

```json
{
  "nodes": [ ... ],
  "edges": [ ... ],
  "source": "supabase"
}
```

---

### `GET /network-map/tree`

Returns the network topology as a hierarchical tree.

**Parameters:** None

**Response:** Tree structure (list of root nodes with nested `children`).

---

### `GET /network-map/nodes`

Returns all device nodes.

**Parameters:** None

**Response:** Node list from Supabase or in-memory fallback.

---

### `GET /network-map/edges`

Returns all network edges.

**Parameters:** None

**Response:** Edge list from Supabase or in-memory fallback.

---

## 16. Database (Supabase)

Prefix: `/db`

Direct Supabase database operations for persistent storage.

---

### `GET /db/schema`

Returns the raw SQL schema file as plain text.

**Parameters:** None

**Response:** `text/plain` — raw SQL DDL statements.

---

### `POST /db/seed`

Seeds the Supabase database with pre-generated sample data.

**Parameters:** None

**Response:**

```json
{
  "devices": 10,
  "topology": 9,
  "telemetry": 150,
  "features": 10,
  "trust_history": 50,
  "alerts": 5
}
```

---

### `POST /db/seed-from-pipeline`

Syncs the current in-memory pipeline state to Supabase.

**Parameters:** None

**Response:**

```json
{
  "devices": 10,
  "telemetry": 180,
  "features": 70,
  "trust_scores": 10,
  "alerts": 5
}
```

---

### `GET /db/devices`

Lists all devices stored in Supabase.

**Parameters:** None

**Response:** Device rows from Supabase.

---

### `GET /db/devices/{device_id}`

Returns a single device from Supabase by ID.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** Device row.

**Errors:** `404` if not found.

---

### `GET /db/devices/{device_id}/telemetry`

Returns telemetry records for a device from Supabase.

| Parameter   | In    | Type     | Required | Default | Constraints |
|-------------|-------|----------|----------|---------|-------------|
| `device_id` | path  | `string` | yes      | —       |             |
| `limit`     | query | `int`    | no       | `50`    | max `500`   |

**Response:** Telemetry rows.

---

### `GET /db/devices/{device_id}/features`

Returns the latest features for a device from Supabase.

| Parameter   | In   | Type     | Required |
|-------------|------|----------|----------|
| `device_id` | path | `string` | yes      |

**Response:** Feature row.

---

### `GET /db/devices/{device_id}/trust-history`

Returns trust score history for a device from Supabase.

| Parameter   | In    | Type     | Required | Default | Constraints |
|-------------|-------|----------|----------|---------|-------------|
| `device_id` | path  | `string` | yes      | —       |             |
| `limit`     | query | `int`    | no       | `50`    | max `500`   |

**Response:** Trust history rows.

---

### `GET /db/alerts`

Lists alerts from Supabase.

| Parameter   | In    | Type     | Required | Default | Constraints |
|-------------|-------|----------|----------|---------|-------------|
| `device_id` | query | `string` | no       | —       |             |
| `severity`  | query | `string` | no       | —       |             |
| `limit`     | query | `int`    | no       | `100`   | max `500`   |

**Response:** Alert rows.

---

### `POST /db/alerts/{alert_id}/resolve`

Marks an alert as resolved in Supabase.

| Parameter  | In   | Type     | Required |
|------------|------|----------|----------|
| `alert_id` | path | `string` | yes      |

**Response:** Resolved alert row.

---

### `GET /db/topology`

Returns the full network topology from Supabase.

**Parameters:** None

**Response:** Topology edge rows.

---

### `GET /db/device-map`

Returns the device name to UUID mapping used for Supabase sync.

**Parameters:** None

**Response:**

```json
{
  "camera-01": "550e8400-e29b-41d4-a716-446655440000",
  "router-01": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  ...
}
```

---

## 17. Enums Reference

### `DeviceType`

```
camera | printer | router | laptop | smart_tv | thermostat | smart_door_lock | smart_light_hub | temperature_sensor | network_gateway
```

### `Protocol`

```
RTSP | HTTPS | HTTP | DNS | NTP | SSH | TELNET | FTP | IPP | MDNS | DHCP | QUIC | UDP | TCP | WEBSOCKET | GIT | MQTT | COAP | ZIGBEE | BLUETOOTH
```

### `DestinationType`

```
INTERNAL | TRUSTED_CLOUD | UNKNOWN_EXTERNAL
```

### `RiskLevel`

```
SAFE | LOW | MEDIUM | HIGH
```

### `DriftSeverity`

```
none | low | medium | high | critical
```

### `PolicyType`

```
protocol_blacklist | destination_restriction | traffic_ceiling | session_limit | traffic_direction
```

### `Confidence`

```
high | medium | low
```

### `AlertType`

```
POLICY_VIOLATION | ML_ANOMALY | DRIFT_DETECTED | DRIFT_CONFIRMED | TRUST_DROP | DEVICE_QUARANTINED | POISONING_ATTEMPT | ATTACK_DETECTED
```

### `AlertSeverity`

```
INFO | LOW | MEDIUM | HIGH | CRITICAL
```

### `EventCategory`

```
SYSTEM | TELEMETRY | DETECTION | POLICY | TRUST | PROTECTION | ATTACK
```

### `GateDecision`

```
allowed | denied | quarantined
```

### `ProtectionStatus`

```
learning | frozen | quarantined
```

---

## 18. Models Reference

Quick-reference for all Pydantic response models and their fields.

### `TelemetryRecord`

| Field              | Type               |
|--------------------|--------------------|
| `record_id`        | `string`           |
| `device_id`        | `string`           |
| `device_type`      | `DeviceType`       |
| `src_ip`           | `string`           |
| `dst_ip`           | `string`           |
| `protocol`         | `Protocol`         |
| `bytes_sent`       | `int` (≥ 0)        |
| `bytes_received`   | `int` (≥ 0)        |
| `session_duration` | `float` (≥ 0)      |
| `packet_count`     | `int` (≥ 0)        |
| `destination_type` | `DestinationType`  |
| `timestamp`        | `datetime`         |
| `window_id`        | `int | null`       |

### `DeviceState`

| Field            | Type             |
|------------------|------------------|
| `device_id`      | `string`         |
| `device_type`    | `DeviceType`     |
| `ip_address`     | `string`         |
| `is_compromised` | `bool`           |
| `active_attack`  | `string | null`  |
| `last_seen`      | `datetime | null` |
| `total_records`  | `int`            |

### `TelemetrySummary`

| Field                    | Type                |
|--------------------------|---------------------|
| `total_records`          | `int`               |
| `total_devices`          | `int`               |
| `records_by_device_type` | `dict[string, int]` |
| `protocols_observed`     | `string[]`          |
| `time_range_start`       | `datetime | null`   |
| `time_range_end`         | `datetime | null`   |

### `DeviceFeatureVector`

| Field                      | Type                   |
|----------------------------|------------------------|
| `device_id`                | `string`               |
| `device_type`              | `DeviceType`           |
| `window_id`                | `int`                  |
| `packet_rate`              | `float`                |
| `avg_session_duration`     | `float`                |
| `total_bytes_sent`         | `int`                  |
| `total_bytes_received`     | `int`                  |
| `traffic_volume`           | `int`                  |
| `unique_destinations`      | `int`                  |
| `destination_entropy`      | `float`                |
| `unique_protocols`         | `int`                  |
| `protocol_entropy`         | `float`                |
| `protocol_distribution`    | `dict[string, float]`  |
| `external_connection_ratio`| `float`                |
| `inbound_outbound_ratio`   | `float`                |
| `record_count`             | `int`                  |
| `window_start`             | `datetime | null`      |
| `window_end`               | `datetime | null`      |

### `DeviceFeatureTimeline`

| Field           | Type                       |
|-----------------|----------------------------|
| `device_id`     | `string`                   |
| `device_type`   | `DeviceType`               |
| `windows`       | `DeviceFeatureVector[]`    |
| `total_windows` | `int`                      |

### `FeatureSummary`

| Field               | Type        |
|---------------------|-------------|
| `total_devices`     | `int`       |
| `total_windows`     | `int`       |
| `features_computed` | `int`       |
| `feature_names`     | `string[]`  |

### `FeatureStats`

| Field     | Type    |
|-----------|---------|
| `mean`    | `float` |
| `std`     | `float` |
| `min_val` | `float` |
| `max_val` | `float` |
| `samples` | `int`   |

### `DeviceBaseline`

| Field                        | Type             |
|------------------------------|------------------|
| `device_id`                  | `string`         |
| `device_type`                | `DeviceType`     |
| `is_frozen`                  | `bool`           |
| `windows_learned`            | `int`            |
| `last_updated`               | `datetime | null` |
| `packet_rate`                | `FeatureStats`   |
| `avg_session_duration`       | `FeatureStats`   |
| `traffic_volume`             | `FeatureStats`   |
| `total_bytes_sent`           | `FeatureStats`   |
| `total_bytes_received`       | `FeatureStats`   |
| `destination_entropy`        | `FeatureStats`   |
| `protocol_entropy`           | `FeatureStats`   |
| `unique_destinations`        | `FeatureStats`   |
| `unique_protocols`           | `FeatureStats`   |
| `external_connection_ratio`  | `FeatureStats`   |
| `inbound_outbound_ratio`     | `FeatureStats`   |
| `allowed_protocols`          | `string[]`       |
| `expected_destination_types` | `string[]`       |

### `DeviceTypeBaseline`

Same as `DeviceBaseline` but keyed by `device_type` instead of `device_id`, with additional `device_count`, `total_windows`, and `traffic_direction` fields.

### `BaselineDeviation`

| Field                      | Type                  |
|----------------------------|-----------------------|
| `device_id`                | `string`              |
| `device_type`              | `DeviceType`          |
| `window_id`                | `int`                 |
| `deviations`               | `dict[string, float]` |
| `max_deviation_feature`    | `string`              |
| `max_deviation_zscore`     | `float`               |
| `features_beyond_threshold`| `string[]`            |
| `threshold_used`           | `float`               |

### `BaselineSummary`

| Field                    | Type       |
|--------------------------|------------|
| `total_device_baselines` | `int`      |
| `total_type_baselines`   | `int`      |
| `frozen_devices`         | `int`      |
| `baseline_phase_windows` | `int`      |
| `device_types_covered`   | `string[]` |

### `FeatureDrift`

| Field                 | Type     |
|-----------------------|----------|
| `feature_name`        | `string` |
| `z_score`             | `float`  |
| `abs_z_score`         | `float`  |
| `baseline_mean`       | `float`  |
| `baseline_std`        | `float`  |
| `current_value`       | `float`  |
| `is_drifting`         | `bool`   |
| `consecutive_windows` | `int`    |

### `DriftResult`

| Field                        | Type               |
|------------------------------|--------------------|
| `device_id`                  | `string`           |
| `device_type`                | `DeviceType`       |
| `window_id`                  | `int`              |
| `timestamp`                  | `datetime`         |
| `is_drifting`                | `bool`             |
| `severity`                   | `DriftSeverity`    |
| `drift_score`                | `float`            |
| `consecutive_drift_windows`  | `int`              |
| `drifting_features`          | `FeatureDrift[]`   |
| `top_drifting_feature`       | `string | null`    |
| `top_z_score`                | `float`            |
| `total_features_checked`     | `int`              |
| `features_beyond_threshold`  | `int`              |

### `DeviceDriftState`

| Field                            | Type              |
|----------------------------------|-------------------|
| `device_id`                      | `string`          |
| `device_type`                    | `DeviceType`      |
| `current_severity`               | `DriftSeverity`   |
| `is_drifting`                    | `bool`            |
| `consecutive_drift_windows`      | `int`             |
| `max_consecutive_drift`          | `int`             |
| `total_drift_windows`            | `int`             |
| `total_windows_analyzed`         | `int`             |
| `latest_drift_score`             | `float`           |
| `peak_drift_score`               | `float`           |
| `currently_drifting_features`    | `string[]`        |
| `historically_drifted_features`  | `string[]`        |
| `first_drift_detected`           | `datetime | null` |
| `last_drift_detected`            | `datetime | null` |
| `drift_confirmed_at`             | `datetime | null` |

### `DriftEvent`

| Field               | Type             |
|---------------------|------------------|
| `event_id`          | `string`         |
| `device_id`         | `string`         |
| `device_type`       | `DeviceType`     |
| `event_type`        | `string`         |
| `severity`          | `DriftSeverity`  |
| `drift_score`       | `float`          |
| `window_id`         | `int`            |
| `timestamp`         | `datetime`       |
| `drifting_features` | `string[]`       |
| `description`       | `string`         |

### `DriftSummary`

| Field                       | Type                  |
|-----------------------------|-----------------------|
| `total_devices_monitored`   | `int`                 |
| `devices_currently_drifting`| `int`                 |
| `devices_by_severity`       | `dict[string, int]`   |
| `total_drift_events`        | `int`                 |
| `confirmation_windows`      | `int`                 |
| `z_score_threshold`         | `float`               |

### `PolicyRule`

| Field         | Type          |
|---------------|---------------|
| `rule_id`     | `string`      |
| `policy_type` | `PolicyType`  |
| `device_type` | `DeviceType`  |
| `description` | `string`      |
| `confidence`  | `Confidence`  |
| `parameters`  | `dict`        |

### `PolicyViolation`

| Field          | Type          |
|----------------|---------------|
| `violation_id` | `string`      |
| `rule_id`      | `string`      |
| `policy_type`  | `PolicyType`  |
| `device_id`    | `string`      |
| `device_type`  | `DeviceType`  |
| `confidence`   | `Confidence`  |
| `description`  | `string`      |
| `evidence`     | `dict`        |
| `record_id`    | `string`      |
| `timestamp`    | `datetime`    |

### `DevicePolicyState`

| Field                     | Type                  |
|---------------------------|-----------------------|
| `device_id`               | `string`              |
| `device_type`             | `DeviceType`          |
| `total_records_evaluated` | `int`                 |
| `total_violations`        | `int`                 |
| `violations_by_type`      | `dict[string, int]`   |
| `violation_rate`          | `float`               |
| `last_violation`          | `datetime | null`     |
| `is_compliant`            | `bool`                |

### `PolicySummary`

| Field                      | Type                |
|----------------------------|---------------------|
| `total_rules`              | `int`               |
| `rules_by_type`            | `dict[string, int]` |
| `rules_by_device_type`     | `dict[string, int]` |
| `total_violations`         | `int`               |
| `devices_with_violations`  | `int`               |
| `total_records_evaluated`  | `int`               |

### `AnomalyScore`

| Field                   | Type                   |
|-------------------------|------------------------|
| `device_id`             | `string`               |
| `device_type`           | `DeviceType`           |
| `window_id`             | `int`                  |
| `anomaly_score`         | `float`                |
| `raw_score`             | `float`                |
| `is_anomalous`          | `bool`                 |
| `threshold`             | `float`                |
| `feature_contributions` | `dict[string, float]`  |
| `timestamp`             | `datetime`             |

### `MLModelInfo`

| Field               | Type              |
|---------------------|-------------------|
| `model_type`        | `string`          |
| `training_samples`  | `int`             |
| `training_features` | `string[]`        |
| `contamination`     | `float`           |
| `trained_at`        | `datetime | null` |
| `dataset_source`    | `string`          |
| `benign_samples`    | `int`             |
| `malicious_samples` | `int`             |

### `MLSummary`

| Field                | Type                |
|----------------------|---------------------|
| `model_loaded`       | `bool`              |
| `model_info`         | `MLModelInfo | null` |
| `total_scored`       | `int`               |
| `anomalies_detected` | `int`               |
| `anomaly_rate`       | `float`             |

### `SignalBreakdown`

| Field                         | Type    |
|-------------------------------|---------|
| `ml_anomaly_score`            | `float` |
| `ml_penalty`                  | `float` |
| `drift_score`                 | `float` |
| `drift_normalized`            | `float` |
| `drift_penalty`               | `float` |
| `drift_confirmed`             | `bool`  |
| `drift_confirmation_penalty`  | `float` |
| `policy_violations_total`     | `int`   |
| `policy_high_confidence`      | `int`   |
| `policy_penalty`              | `float` |
| `total_penalty`               | `float` |

### `DeviceTrustScore`

| Field                    | Type               |
|--------------------------|--------------------|
| `device_id`              | `string`           |
| `device_type`            | `DeviceType`       |
| `trust_score`            | `float`            |
| `risk_level`             | `RiskLevel`        |
| `signal_breakdown`       | `SignalBreakdown`  |
| `baseline_update_allowed`| `bool`             |
| `timestamp`              | `datetime`         |

### `DeviceTrustHistory`

| Field           | Type                    |
|-----------------|-------------------------|
| `device_id`     | `string`                |
| `device_type`   | `DeviceType`            |
| `scores`        | `DeviceTrustScore[]`    |
| `current_score` | `float`                 |
| `current_risk`  | `RiskLevel`             |
| `lowest_score`  | `float`                 |
| `highest_score` | `float`                 |
| `average_score` | `float`                 |

### `TrustSummary`

| Field                      | Type                   |
|----------------------------|------------------------|
| `total_devices`            | `int`                  |
| `devices_by_risk`          | `dict[string, int]`    |
| `average_trust`            | `float`                |
| `lowest_trust_device`      | `string | null`        |
| `lowest_trust_score`       | `float`                |
| `baseline_updates_blocked` | `int`                  |
| `weights`                  | `dict[string, float]`  |

### `GateEvent`

| Field         | Type             |
|---------------|------------------|
| `device_id`   | `string`         |
| `device_type` | `DeviceType`     |
| `decision`    | `GateDecision`   |
| `trust_score` | `float`          |
| `threshold`   | `float`          |
| `reason`      | `string`         |
| `timestamp`   | `datetime`       |

### `PoisoningAttempt`

| Field                   | Type               |
|-------------------------|--------------------|
| `device_id`             | `string`           |
| `device_type`           | `DeviceType`       |
| `trust_score_at_time`   | `float`            |
| `protection_status`     | `ProtectionStatus` |
| `feature_drift_detected`| `bool`             |
| `reason`                | `string`           |
| `timestamp`             | `datetime`         |

### `DeviceProtectionState`

| Field                 | Type                   |
|-----------------------|------------------------|
| `device_id`           | `string`               |
| `device_type`         | `DeviceType`           |
| `status`              | `ProtectionStatus`     |
| `is_frozen`           | `bool`                 |
| `is_quarantined`      | `bool`                 |
| `trust_score`         | `float`                |
| `consecutive_denied`  | `int`                  |
| `total_allowed`       | `int`                  |
| `total_denied`        | `int`                  |
| `poisoning_attempts`  | `int`                  |
| `baseline_integrity`  | `float`                |
| `last_allowed_update` | `datetime | null`      |
| `last_decision`       | `GateDecision | null`  |
| `last_decision_time`  | `datetime | null`      |

### `ProtectionSummary`

| Field                      | Type    |
|----------------------------|---------|
| `total_devices`            | `int`   |
| `devices_learning`         | `int`   |
| `devices_frozen`           | `int`   |
| `devices_quarantined`      | `int`   |
| `total_gate_events`        | `int`   |
| `total_allowed`            | `int`   |
| `total_denied`             | `int`   |
| `total_poisoning_attempts` | `int`   |
| `average_integrity`        | `float` |
| `quarantine_threshold`     | `int`   |
| `trust_gate_threshold`     | `float` |

### `Alert`

| Field                | Type              |
|----------------------|-------------------|
| `alert_id`           | `string`          |
| `alert_type`         | `AlertType`       |
| `severity`           | `AlertSeverity`   |
| `device_id`          | `string`          |
| `device_type`        | `DeviceType`      |
| `title`              | `string`          |
| `reason`             | `string`          |
| `evidence`           | `dict`            |
| `trust_score_at_time`| `float | null`    |
| `timestamp`          | `datetime`        |
| `acknowledged`       | `bool`            |

### `AlertSummary`

| Field            | Type                |
|------------------|---------------------|
| `total_alerts`   | `int`               |
| `by_type`        | `dict[string, int]` |
| `by_severity`    | `dict[string, int]` |
| `by_device`      | `dict[string, int]` |
| `unacknowledged` | `int`               |
| `most_recent`    | `datetime | null`   |

### `Event`

| Field         | Type                |
|---------------|---------------------|
| `event_id`    | `string`            |
| `category`    | `EventCategory`     |
| `event_type`  | `string`            |
| `device_id`   | `string | null`     |
| `device_type` | `DeviceType | null` |
| `description` | `string`            |
| `metadata`    | `dict`              |
| `timestamp`   | `datetime`          |

### `EventSummary`

| Field          | Type                |
|----------------|---------------------|
| `total_events` | `int`               |
| `by_category`  | `dict[string, int]` |
| `by_device`    | `dict[string, int]` |
| `earliest`     | `datetime | null`   |
| `latest`       | `datetime | null`   |

### `AttackRequest`

| Field         | Type     | Default |
|---------------|----------|---------|
| `device_id`   | `string` | —       |
| `attack_type` | `string` | —       |
| `cycles`      | `int`    | `3`     |
