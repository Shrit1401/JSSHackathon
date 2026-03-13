# IoT Trust Monitor — API Reference for Frontend

**Base URL:** `https://bf52-2401-4900-c9a1-6649-2817-3cba-d53c-924.ngrok-free.app`

**CORS:** Allowed origin is `http://localhost:3000`. For ngrok, you may need to add the ngrok URL to CORS in `main.py` if you hit CORS errors from a different origin.

---

## Health

| Method | Endpoint  | Description                                 |
| ------ | --------- | ------------------------------------------- |
| `GET`  | `/health` | Liveness check. Returns `{"status": "ok"}`. |

---

## Devices

### Dashboard overview

| Method | Endpoint    | Description                                                                             |
| ------ | ----------- | --------------------------------------------------------------------------------------- |
| `GET`  | `/overview` | Dashboard counts: total devices, risk breakdown (safe/low/medium/high), online/offline. |

**Response:** `OverviewStats`

```json
{
  "total_devices": 10,
  "safe": 5,
  "low": 2,
  "medium": 2,
  "high": 1,
  "online": 8,
  "offline": 2
}
```

---

### List all devices

| Method | Endpoint   | Description                                      |
| ------ | ---------- | ------------------------------------------------ |
| `GET`  | `/devices` | All IoT devices with trust score and risk level. |

**Response:** Array of `DeviceSummary`

```json
[
  {
    "id": "uuid",
    "name": "Living Room Camera",
    "device_type": "camera",
    "ip_address": "192.168.1.101",
    "vendor": "VendorName",
    "trust_score": 85,
    "risk_level": "LOW",
    "traffic_rate": 12.5,
    "status": "online",
    "last_seen": "2025-03-13T10:00:00.000Z"
  }
]
```

`risk_level` is one of: `"SAFE"`, `"LOW"`, `"MEDIUM"`, `"HIGH"`.

---

### Add a device

| Method | Endpoint   | Description                                                                                   |
| ------ | ---------- | --------------------------------------------------------------------------------------------- |
| `POST` | `/devices` | Register a new device. Trust defaults to 100; risk is computed. Returns created device (201). |

**Request body:** `AddDeviceRequest`

```json
{
  "name": "New Sensor",
  "device_type": "sensor",
  "ip_address": "192.168.1.50",
  "vendor": "Acme",
  "trust_score": 100,
  "traffic_rate": 0.0,
  "status": "online"
}
```

- `trust_score` (optional, default 100), `traffic_rate` (optional, default 0.0), `status` (optional, default `"online"`).

**Response (201):** `AddDeviceResponse` — full device row including `id`, `created_at`, `last_seen`, `risk_level`.

---

### Device detail

| Method | Endpoint               | Description                                                     |
| ------ | ---------------------- | --------------------------------------------------------------- |
| `GET`  | `/devices/{device_id}` | Full device + open ports, protocol usage, security explanation. |

**Response:** `DeviceDetail`

```json
{
  "id": "uuid",
  "name": "Living Room Camera",
  "device_type": "camera",
  "ip_address": "192.168.1.101",
  "vendor": "VendorName",
  "trust_score": 85,
  "risk_level": "LOW",
  "traffic_rate": 12.5,
  "status": "online",
  "last_seen": "2025-03-13T10:00:00.000Z",
  "created_at": "2025-01-01T00:00:00.000Z",
  "open_ports": ["80", "443", "554"],
  "protocol_usage": { "HTTP": 0.6, "HTTPS": 0.3, "RTSP": 0.1 },
  "security_explanation": "Plain English explanation of current risk..."
}
```

---

### Device security explanation

| Method | Endpoint                       | Description                                                 |
| ------ | ------------------------------ | ----------------------------------------------------------- |
| `GET`  | `/devices/{device_id}/explain` | Why this device has its current risk level (plain English). |

**Response:** `ExplainResponse`

```json
{
  "device_id": "uuid",
  "device_name": "Living Room Camera",
  "risk_level": "LOW",
  "trust_score": 85,
  "explanation": "Plain English explanation..."
}
```

---

### Network map (topology)

| Method | Endpoint       | Description                                                                                               |
| ------ | -------------- | --------------------------------------------------------------------------------------------------------- |
| `GET`  | `/network-map` | Nodes (devices) and edges for a network graph. Non-gateway devices connect to the primary gateway/router. |

**Response:** `NetworkMap`

```json
{
  "nodes": [
    {
      "id": "uuid",
      "name": "Router",
      "device_type": "router",
      "risk_level": "SAFE",
      "trust_score": 100,
      "status": "online"
    }
  ],
  "edges": [{ "source": "gateway-uuid", "target": "device-uuid" }]
}
```

---

## Alerts

| Method | Endpoint  | Description                            |
| ------ | --------- | -------------------------------------- |
| `GET`  | `/alerts` | Last 50 security alerts, newest first. |

**Response:** Array of `AlertOut`

```json
[
  {
    "id": "uuid",
    "device_id": "device-uuid",
    "device_name": "Living Room Camera",
    "alert_type": "TRAFFIC_SPIKE",
    "severity": "HIGH",
    "message": "Alert description...",
    "timestamp": "2025-03-13T10:00:00.000Z"
  }
]
```

---

## Events

| Method | Endpoint  | Description                                                  |
| ------ | --------- | ------------------------------------------------------------ |
| `GET`  | `/events` | Last 100 device events (including simulation), newest first. |

**Response:** Array of `EventOut`

```json
[
  {
    "id": "uuid",
    "device_id": "device-uuid",
    "event_type": "TRAFFIC_SPIKE",
    "description": "[Auto] TRAFFIC_SPIKE detected on Living Room Camera",
    "timestamp": "2025-03-13T10:00:00.000Z"
  }
]
```

`event_type` can be: `TRAFFIC_SPIKE`, `POLICY_VIOLATION`, `NEW_DESTINATION`, `BACKDOOR`, `DATA_EXFILTRATION`.

---

## Simulation (attack simulation)

All simulation endpoints expect the same request body.

**Request body:** `SimulateAttackRequest`

```json
{
  "device_id": "uuid-of-device",
  "attack_type": "TRAFFIC_SPIKE"
}
```

- `attack_type` is optional. If omitted on `/simulate-attack`, a random type is used.
- Valid `attack_type`: `TRAFFIC_SPIKE`, `POLICY_VIOLATION`, `NEW_DESTINATION`, `BACKDOOR`, `DATA_EXFILTRATION`.

**Response (all):** `SimulateAttackResponse`

```json
{
  "device_id": "uuid",
  "attack_type": "TRAFFIC_SPIKE",
  "old_trust_score": 85,
  "new_trust_score": 65,
  "old_risk_level": "LOW",
  "new_risk_level": "MEDIUM",
  "alert_created": true,
  "message": "TRAFFIC_SPIKE simulated on 'Device Name'. Trust dropped 85 → 65. Risk: LOW → MEDIUM."
}
```

---

### Generic simulate attack

| Method | Endpoint           | Description                                                                                                                                |
| ------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `POST` | `/simulate-attack` | Simulate any attack on a device. If `attack_type` is omitted, one is chosen at random. Updates trust/risk, event, and may create an alert. |

---

### Dedicated attack endpoints (always create an alert)

| Method | Endpoint                      | Description                                                                                          |
| ------ | ----------------------------- | ---------------------------------------------------------------------------------------------------- |
| `POST` | `/simulate/backdoor`          | Backdoor implant. Trust drops 25–40, traffic +2–8 MB/s, status set to `compromised`, CRITICAL alert. |
| `POST` | `/simulate/traffic-spike`     | Traffic flood / DDoS. Trust drops 10–20, traffic +15–40 MB/s, HIGH alert.                            |
| `POST` | `/simulate/data-exfiltration` | Data exfiltration. Trust drops 15–25, traffic +10–25 MB/s, HIGH alert.                               |

Same request body: `{ "device_id": "uuid", "attack_type": "BACKDOOR" }` (attack_type optional on generic endpoint only; on dedicated endpoints it’s fixed by the path).

---

## Error responses

- **404** — Device not found: `{"detail": "Device 'id' not found"}`
- **422** — Validation / invalid `attack_type`: `{"detail": "Invalid attack_type 'X'. Must be one of: [...]"}`
- **502** — Database error: `{"detail": "Database error"}`
- **500** — Server error: `{"detail": "Internal server error. Check server logs for details."}`

---

## Quick checklist for frontend

- [ ] **Dashboard:** `GET /overview` for counts and risk breakdown.
- [ ] **Device list:** `GET /devices` for table/cards; link to `/devices/{id}` for detail.
- [ ] **Device detail page:** `GET /devices/{id}` (full detail + ports + explanation); optional `GET /devices/{id}/explain` for explanation only.
- [ ] **Add device form:** `POST /devices` with name, device_type, ip_address, vendor (+ optional trust_score, traffic_rate, status).
- [ ] **Network graph:** `GET /network-map` for nodes and edges.
- [ ] **Alerts feed:** `GET /alerts` (50 most recent).
- [ ] **Events feed:** `GET /events` (100 most recent).
- [ ] **Simulate attack (generic):** `POST /simulate-attack` with `device_id` and optional `attack_type`.
- [ ] **Simulate specific attacks:** `POST /simulate/backdoor`, `POST /simulate/traffic-spike`, `POST /simulate/data-exfiltration` with `device_id` (and optional `attack_type` in body).

Use the base URL above for all requests. For interactive API docs, open **`/docs`** (Swagger UI) or **`/redoc`** (ReDoc) on the same base URL.
