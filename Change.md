# Change log (uncommitted)

Summary of **uncommitted changes** in the `jss` (IoT Trust Monitor) backend.

---

## Modified files

- `app/models/device_models.py`
- `app/routers/devices.py`
- `app/routers/simulation.py`

*(Previously tracked `CHANGES.md` was removed.)*

---

## 1. `app/models/device_models.py`

### AddDeviceRequest
- **Added:** `parent_id: Optional[str] = None` — optional parent device for hierarchy.

### AddDeviceResponse
- **Added:** `parent_id: Optional[str] = None` — returned when adding a device.

### SimulateAttackRequest
- **Added:** `stealth_level: Optional[Literal["low", "medium", "high"]] = "medium"` — controls backdoor stealth (affects trust/traffic/detection).

### SimulateAttackResponse
- **Added:** `detection_difficulty: Optional[int] = None` — difficulty of detecting the simulated attack.

---

## 2. `app/routers/devices.py`

### Add device
- **Added:** `parent_id` from the request body is stored when creating a device.

### Network map (`get_network_map`)
- **Before:** Single “hub” (first router/gateway), all other devices connected to that hub.
- **After:**
  - Chooses gateway → router → hub in that order as fallback roots.
  - Uses a **PARENT_MAP** by `device_type`: gateway (no parent), router → gateway, hub → router, cameras/sensors/smart_tv/thermostat → hub, laptop/printer/smartphone → router.
  - Each device’s edge uses `parent_id` when set, otherwise `PARENT_MAP[device_type]`, otherwise gateway.
  - Edges only added when `parent_id != device_id` (no self-edges).

---

## 3. `app/routers/simulation.py`

### Backdoor presets
- **Added:** `BACKDOOR_PRESETS` dict keyed by `"low" | "medium" | "high"` with:
  - `trust_low` / `trust_high` — trust score delta range
  - `traffic_low` / `traffic_high` — traffic delta range
  - `detection` — detection difficulty (e.g. 85 / 50 / 20).

### `_run_dedicated_attack`
- **Added parameters:** `trust_delta_low`, `trust_delta_high`, `detection_difficulty`.
- **Behavior:** If `trust_delta_low`/`trust_delta_high` are set, new trust = `old_trust + random(trust_delta_low, trust_delta_high)` (clamped ≥ 0); otherwise unchanged `adjust_trust_score` logic.
- **Response:** `detection_difficulty` is included in `SimulateAttackResponse`.

### Backdoor simulation (`simulate_backdoor`)
- **Uses:** `body.stealth_level` (default `"medium"`) to select a preset from `BACKDOOR_PRESETS`.
- **Passes:** Preset’s `traffic_low`/`traffic_high`, `trust_low`/`trust_high`, and `detection` into `_run_dedicated_attack` so backdoor behavior and detection difficulty depend on stealth level.
