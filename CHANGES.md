# Changes Summary

This document lists the **uncommitted changes** in the `jss` (IoT Trust Monitor) backend, relative to the last commit:  
`43606f5 Backend: IoT Trust Monitor API - devices, alerts, events, simulation`.

---

## Modified Files

- `app/main.py`
- `app/models/device_models.py`
- `app/routers/simulation.py`
- `app/services/trust_engine.py`

---

## 1. `app/main.py`

### Removed
- Imports: `ssl`, `certifi`
- Imports from `trust_engine`: `adjust_trust_score`, `build_alert_payload`, `should_create_alert`
- Module-level constant: `ATTACK_TYPES`

### Added
- Import from `trust_engine`: `recover_trust_score`

### Behavior: background simulation tick
- **Before:** Each tick picked a random device and a random attack type, applied `adjust_trust_score`, updated device + inserted event, and sometimes created an alert via `should_create_alert` / `build_alert_payload`.
- **After:**
  - **~85% of ticks:** “Normal” behavior — small traffic fluctuation and **trust recovery** via `recover_trust_score` (no event, no alert). Log level `debug` with message `(normal)`.
  - **~15% of ticks:** “Minor anomaly” — small trust dip (random -5 to -1), small traffic bump, **no alert**. Inserts an event with type `TRAFFIC_FLUCTUATION` and description `"[Auto] Minor traffic fluctuation on {name}"`. Log level `debug` with message `(minor anomaly)`.
- Alerts are **no longer created** from the background tick; only device updates and (for minor anomaly) one event type.

---

## 2. `app/models/device_models.py`

### Risk level type
- **Before:** `risk_level` was `Literal["SAFE", "LOW", "MEDIUM", "HIGH"]`.
- **After:** `risk_level` is `Literal["SAFE", "LOW", "MEDIUM", "HIGH", "COMPROMISED"]` everywhere it appears:
  - `DeviceSummary`
  - `DeviceDetail`
  - `NetworkNode`
  - `AddDeviceResponse`
  - `ExplainResponse`

---

## 3. `app/routers/simulation.py`

### Generic simulate-attack
- **Before:** New trust was computed with `adjust_trust_score(old_trust, attack_type)` (attack-type–dependent).
- **After:** New trust is computed with `apply_attack_penalty(old_trust)` (fixed strong penalty; see trust_engine).

### New endpoint: reset network
- **Added:** `POST /reset-network` — “Reset all devices to healthy state”.
- Fetches all device IDs from the `devices` table, then for each device updates:
  - `trust_score`: random 85–95
  - `risk_level`: `"SAFE"`
  - `status`: `"online"`
  - `last_seen`: current UTC timestamp
- Returns `{"message": "Reset N devices to healthy state.", "devices_reset": N}`.
- Errors: 502 on DB fetch failure; logs and continues on per-device update failure.

### Imports
- **Added:** `apply_attack_penalty` from `app.services.trust_engine`.

---

## 4. `app/services/trust_engine.py`

### Risk level for low trust
- **Before:** `compute_risk_level` returned `"HIGH"` for scores &lt; 40.
- **After:** It returns `"COMPROMISED"` for scores &lt; 40.

### New helpers
- **`apply_attack_penalty(current: int) -> int`**  
  Strong penalty for the generic simulate-attack: adds a random delta between -60 and -40, then clamps to [0, 100].
- **`recover_trust_score(current: int) -> int`**  
  Used by the background tick for “normal” behavior: if `current >= 90` returns `current`; otherwise adds a random 1–3 and caps at 100 (slow recovery toward 90).
- **`NORMAL_EVENT_TYPES`**  
  List: `["ROUTINE_SCAN", "HEARTBEAT", "CONFIG_SYNC", "TRAFFIC_FLUCTUATION"]` (for reference; not yet used in the tick logic beyond the new event type).

### Security explanation
- **Before:** The “low trust” branch referred to `HIGH` in the explanation text.
- **After:** That branch is labeled as `COMPROMISED` in the generated explanation.

### Seed devices
- All listed seed devices were adjusted to **healthier** defaults:
  - Trust scores increased (e.g. 72→90, 55→87, 35→86, 28→93).
  - Risk levels set to `"SAFE"` where they were LOW/MEDIUM/HIGH.
  - Some `traffic_rate` values reduced (e.g. 15.7→5.7, 22.9→2.9, 31.2→7.2).

---

## Summary Table

| Area              | Change                                                                 |
|-------------------|------------------------------------------------------------------------|
| **Risk levels**   | New value `COMPROMISED` for score &lt; 40; models and explanations updated. |
| **Background tick** | No more random attacks; mostly trust recovery; occasional minor anomaly (TRAFFIC_FLUCTUATION, no alert). |
| **Simulate attack** | Uses `apply_attack_penalty` (fixed -40 to -60) instead of attack-type–specific. |
| **New API**       | `POST /reset-network` to reset all devices to a healthy state.         |
| **Seed data**     | All seed devices have higher trust and SAFE risk.                      |

---

*Generated from `git diff` on branch `backend` (uncommitted changes).*
