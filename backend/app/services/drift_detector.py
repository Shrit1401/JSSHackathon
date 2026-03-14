import uuid
from datetime import datetime
from collections import defaultdict
from typing import Optional

from app.models.telemetry import DeviceType
from app.models.features import DeviceFeatureVector
from app.models.baseline import FeatureStats
from app.models.drift import (
    DriftSeverity,
    FeatureDrift,
    DriftResult,
    DeviceDriftState,
    DriftEvent,
    DriftSummary,
)
from app.services.baseline_engine import BaselineEngine, NUMERIC_FEATURES

CONFIRMATION_WINDOWS = 3
Z_SCORE_THRESHOLD = 3.0

SEVERITY_THRESHOLDS = {
    DriftSeverity.LOW: 3.0,
    DriftSeverity.MEDIUM: 5.0,
    DriftSeverity.HIGH: 10.0,
    DriftSeverity.CRITICAL: 20.0,
}


def _classify_severity(drift_score: float, consecutive: int) -> DriftSeverity:
    if drift_score < SEVERITY_THRESHOLDS[DriftSeverity.LOW]:
        return DriftSeverity.NONE

    if consecutive < CONFIRMATION_WINDOWS:
        if drift_score >= SEVERITY_THRESHOLDS[DriftSeverity.CRITICAL]:
            return DriftSeverity.HIGH
        if drift_score >= SEVERITY_THRESHOLDS[DriftSeverity.HIGH]:
            return DriftSeverity.MEDIUM
        return DriftSeverity.LOW

    if drift_score >= SEVERITY_THRESHOLDS[DriftSeverity.CRITICAL]:
        return DriftSeverity.CRITICAL
    if drift_score >= SEVERITY_THRESHOLDS[DriftSeverity.HIGH]:
        return DriftSeverity.HIGH
    if drift_score >= SEVERITY_THRESHOLDS[DriftSeverity.MEDIUM]:
        return DriftSeverity.MEDIUM
    return DriftSeverity.LOW


class DriftDetector:
    def __init__(self, baseline_engine: BaselineEngine):
        self.baseline_engine = baseline_engine
        self.device_states: dict[str, DeviceDriftState] = {}
        self.feature_streak: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.events: list[DriftEvent] = []
        self.results_history: dict[str, list[DriftResult]] = defaultdict(list)

    def _get_baseline_stats(self, device_id: str, device_type: DeviceType) -> Optional[object]:
        bl = self.baseline_engine.get_device_baseline(device_id)
        if bl:
            return bl
        return self.baseline_engine.get_type_baseline(device_type)

    def _compute_feature_drifts(self, fv: DeviceFeatureVector, baseline) -> list[FeatureDrift]:
        device_id = fv.device_id
        drifts = []

        for feat in NUMERIC_FEATURES:
            current = getattr(fv, feat)
            stats: FeatureStats = getattr(baseline, feat)

            if stats.std > 0:
                z = (current - stats.mean) / stats.std
            else:
                z = 0.0 if current == stats.mean else 10.0

            abs_z = abs(z)
            is_feat_drifting = abs_z > Z_SCORE_THRESHOLD

            if is_feat_drifting:
                self.feature_streak[device_id][feat] += 1
            else:
                self.feature_streak[device_id][feat] = 0

            drifts.append(FeatureDrift(
                feature_name=feat,
                z_score=round(z, 4),
                abs_z_score=round(abs_z, 4),
                baseline_mean=stats.mean,
                baseline_std=stats.std,
                current_value=round(current, 4),
                is_drifting=is_feat_drifting,
                consecutive_windows=self.feature_streak[device_id][feat],
            ))

        return drifts

    def _compute_drift_score(self, feature_drifts: list[FeatureDrift]) -> float:
        drifting = [fd for fd in feature_drifts if fd.is_drifting]
        if not drifting:
            return 0.0
        weighted_sum = sum(fd.abs_z_score for fd in drifting)
        breadth_factor = len(drifting) / len(feature_drifts)
        return round(weighted_sum * (1 + breadth_factor), 4)

    def _emit_event(self, device_id: str, device_type: DeviceType, event_type: str,
                    severity: DriftSeverity, drift_score: float, window_id: int,
                    drifting_features: list[str], description: str):
        event = DriftEvent(
            event_id=str(uuid.uuid4()),
            device_id=device_id,
            device_type=device_type,
            event_type=event_type,
            severity=severity,
            drift_score=drift_score,
            window_id=window_id,
            timestamp=datetime.utcnow(),
            drifting_features=drifting_features,
            description=description,
        )
        self.events.append(event)
        return event

    def analyze(self, feature_vector: DeviceFeatureVector) -> DriftResult:
        device_id = feature_vector.device_id
        device_type = feature_vector.device_type
        window_id = feature_vector.window_id

        baseline = self._get_baseline_stats(device_id, device_type)
        if not baseline:
            raise ValueError(f"No baseline for {device_id}")

        feature_drifts = self._compute_feature_drifts(feature_vector, baseline)
        drift_score = self._compute_drift_score(feature_drifts)
        drifting_features = [fd for fd in feature_drifts if fd.is_drifting]
        drifting_names = [fd.feature_name for fd in drifting_features]
        is_drifting = len(drifting_features) > 0

        state = self.device_states.get(device_id)
        if not state:
            state = DeviceDriftState(
                device_id=device_id,
                device_type=device_type,
                current_severity=DriftSeverity.NONE,
                is_drifting=False,
                consecutive_drift_windows=0,
                max_consecutive_drift=0,
                total_drift_windows=0,
                total_windows_analyzed=0,
                latest_drift_score=0.0,
                peak_drift_score=0.0,
                currently_drifting_features=[],
                historically_drifted_features=[],
            )
            self.device_states[device_id] = state

        state.total_windows_analyzed += 1

        if is_drifting:
            state.consecutive_drift_windows += 1
            state.total_drift_windows += 1
            state.max_consecutive_drift = max(state.max_consecutive_drift, state.consecutive_drift_windows)

            if not state.first_drift_detected:
                state.first_drift_detected = datetime.utcnow()
            state.last_drift_detected = datetime.utcnow()

            if state.consecutive_drift_windows == CONFIRMATION_WINDOWS:
                state.drift_confirmed_at = datetime.utcnow()
        else:
            prev_was_drifting = state.is_drifting
            state.consecutive_drift_windows = 0
            if prev_was_drifting:
                self._emit_event(
                    device_id, device_type, "drift_resolved", DriftSeverity.NONE,
                    0.0, window_id, [],
                    f"{device_id} behavior returned to baseline",
                )

        severity = _classify_severity(drift_score, state.consecutive_drift_windows)

        prev_severity = state.current_severity
        state.is_drifting = is_drifting
        state.current_severity = severity
        state.latest_drift_score = drift_score
        state.peak_drift_score = max(state.peak_drift_score, drift_score)
        state.currently_drifting_features = drifting_names

        hist_set = set(state.historically_drifted_features)
        hist_set.update(drifting_names)
        state.historically_drifted_features = sorted(hist_set)

        if is_drifting and state.consecutive_drift_windows == 1:
            self._emit_event(
                device_id, device_type, "drift_detected", severity,
                drift_score, window_id, drifting_names,
                f"{device_id} showing anomalous behavior in {len(drifting_names)} features",
            )

        if is_drifting and state.consecutive_drift_windows == CONFIRMATION_WINDOWS:
            self._emit_event(
                device_id, device_type, "drift_confirmed", severity,
                drift_score, window_id, drifting_names,
                f"{device_id} drift confirmed after {CONFIRMATION_WINDOWS} consecutive windows — "
                f"top deviation: {drifting_features[0].feature_name} (z={drifting_features[0].z_score:+.2f})",
            )

        if is_drifting and severity != prev_severity and state.consecutive_drift_windows > 1:
            self._emit_event(
                device_id, device_type, "severity_escalated", severity,
                drift_score, window_id, drifting_names,
                f"{device_id} drift severity escalated from {prev_severity.value} to {severity.value}",
            )

        top_feature = None
        top_z = 0.0
        if drifting_features:
            top = max(drifting_features, key=lambda fd: fd.abs_z_score)
            top_feature = top.feature_name
            top_z = top.abs_z_score

        result = DriftResult(
            device_id=device_id,
            device_type=device_type,
            window_id=window_id,
            timestamp=datetime.utcnow(),
            is_drifting=is_drifting,
            severity=severity,
            drift_score=drift_score,
            consecutive_drift_windows=state.consecutive_drift_windows,
            drifting_features=feature_drifts,
            top_drifting_feature=top_feature,
            top_z_score=top_z,
            total_features_checked=len(feature_drifts),
            features_beyond_threshold=len(drifting_features),
        )

        self.results_history[device_id].append(result)
        return result

    def analyze_window(self, feature_vectors: list[DeviceFeatureVector]) -> list[DriftResult]:
        return [self.analyze(fv) for fv in feature_vectors]

    def get_device_state(self, device_id: str) -> Optional[DeviceDriftState]:
        return self.device_states.get(device_id)

    def get_all_device_states(self) -> list[DeviceDriftState]:
        return list(self.device_states.values())

    def get_drifting_devices(self) -> list[DeviceDriftState]:
        return [s for s in self.device_states.values() if s.is_drifting]

    def get_device_history(self, device_id: str) -> list[DriftResult]:
        return self.results_history.get(device_id, [])

    def get_events(self, device_id: Optional[str] = None, event_type: Optional[str] = None) -> list[DriftEvent]:
        events = self.events
        if device_id:
            events = [e for e in events if e.device_id == device_id]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events

    def get_summary(self) -> DriftSummary:
        by_severity = defaultdict(int)
        for state in self.device_states.values():
            by_severity[state.current_severity.value] += 1

        return DriftSummary(
            total_devices_monitored=len(self.device_states),
            devices_currently_drifting=len(self.get_drifting_devices()),
            devices_by_severity=dict(by_severity),
            total_drift_events=len(self.events),
            confirmation_windows=CONFIRMATION_WINDOWS,
            z_score_threshold=Z_SCORE_THRESHOLD,
        )

    def reset(self):
        self.device_states.clear()
        self.feature_streak.clear()
        self.events.clear()
        self.results_history.clear()
