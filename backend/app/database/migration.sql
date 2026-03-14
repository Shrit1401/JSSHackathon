-- ═══════════════════════════════════════════════════════════════
--  IoT Sentinel — Full Migration
--  Run this in Supabase Dashboard → SQL Editor → New Query
-- ═══════════════════════════════════════════════════════════════

-- Drop old tables (order matters due to foreign keys)
DROP TABLE IF EXISTS network_topology CASCADE;
DROP TABLE IF EXISTS trust_history CASCADE;
DROP TABLE IF EXISTS device_features CASCADE;
DROP TABLE IF EXISTS telemetry_events CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS devices CASCADE;

-- ───────────────────────────────────────────
--  DEVICES
-- ───────────────────────────────────────────

CREATE TABLE devices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_name     TEXT NOT NULL,
    device_type     TEXT NOT NULL,
    ip_address      TEXT NOT NULL,
    mac_address     TEXT,
    manufacturer    TEXT,
    firmware_version TEXT,
    trust_score     FLOAT DEFAULT 100.0,
    risk_level      TEXT DEFAULT 'SAFE',
    status          TEXT DEFAULT 'safe' CHECK (status IN ('safe', 'suspicious', 'compromised')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_seen       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_devices_trust_score ON devices (trust_score);
CREATE INDEX idx_devices_device_type ON devices (device_type);
CREATE INDEX idx_devices_status ON devices (status);

-- ───────────────────────────────────────────
--  TELEMETRY EVENTS
-- ───────────────────────────────────────────

CREATE TABLE telemetry_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id       UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    protocol        TEXT NOT NULL,
    bytes_sent      BIGINT DEFAULT 0,
    bytes_received  BIGINT DEFAULT 0,
    packet_count    INTEGER DEFAULT 0,
    session_duration FLOAT DEFAULT 0.0,
    destination_ip  TEXT,
    destination_type TEXT CHECK (destination_type IN ('internal', 'trusted_cloud', 'external')),
    timestamp       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_telemetry_device_id ON telemetry_events (device_id);
CREATE INDEX idx_telemetry_timestamp ON telemetry_events (timestamp);

-- ───────────────────────────────────────────
--  DEVICE FEATURES
-- ───────────────────────────────────────────

CREATE TABLE device_features (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id             UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    packet_rate           FLOAT,
    avg_session_duration  FLOAT,
    traffic_volume        BIGINT,
    destination_entropy   FLOAT,
    protocol_entropy      FLOAT,
    calculated_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_features_device_id ON device_features (device_id);
CREATE INDEX idx_features_calculated_at ON device_features (calculated_at);

-- ───────────────────────────────────────────
--  ALERTS
-- ───────────────────────────────────────────

CREATE TABLE alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id       UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    alert_type      TEXT NOT NULL,
    severity        TEXT NOT NULL CHECK (severity IN ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    description     TEXT,
    confidence      FLOAT,
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    resolved        BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_alerts_device_id ON alerts (device_id);
CREATE INDEX idx_alerts_timestamp ON alerts (timestamp);
CREATE INDEX idx_alerts_severity ON alerts (severity);

-- ───────────────────────────────────────────
--  TRUST HISTORY
-- ───────────────────────────────────────────

CREATE TABLE trust_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id       UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    trust_score     FLOAT NOT NULL,
    reason          TEXT,
    timestamp       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trust_history_device_id ON trust_history (device_id);
CREATE INDEX idx_trust_history_timestamp ON trust_history (timestamp);
CREATE INDEX idx_trust_history_trust_score ON trust_history (trust_score);

-- ───────────────────────────────────────────
--  NETWORK TOPOLOGY
-- ───────────────────────────────────────────

CREATE TABLE network_topology (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_device   UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    target_device   UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    connection_type TEXT,
    last_active     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_topology_source ON network_topology (source_device);
CREATE INDEX idx_topology_target ON network_topology (target_device);
