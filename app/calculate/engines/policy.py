import uuid
from datetime import datetime
from collections import defaultdict
from typing import Optional

from ..models import (
    TelemetryRecord, DeviceType, PolicyType, PolicyRule, PolicyViolation,
    RecordEvaluation, DevicePolicyState, Confidence,
)
from ..policy_rules import POLICY_RULES


def _check_protocol_blacklist(record: TelemetryRecord, rule: PolicyRule) -> Optional[PolicyViolation]:
    blocked = rule.parameters["blocked_protocols"]
    if record.protocol.value in blocked:
        return PolicyViolation(
            violation_id=str(uuid.uuid4()), rule_id=rule.rule_id, policy_type=rule.policy_type,
            device_id=record.device_id, device_type=record.device_type, confidence=rule.confidence,
            description=f"{record.device_id} used blacklisted protocol {record.protocol.value}",
            evidence={"protocol_used": record.protocol.value, "blocked_protocols": blocked, "destination_ip": record.dst_ip, "destination_type": record.destination_type.value},
            record_id=record.record_id, timestamp=record.timestamp,
        )
    return None


def _check_destination_restriction(record: TelemetryRecord, rule: PolicyRule) -> Optional[PolicyViolation]:
    blocked = rule.parameters["blocked_destinations"]
    if record.destination_type.value in blocked:
        return PolicyViolation(
            violation_id=str(uuid.uuid4()), rule_id=rule.rule_id, policy_type=rule.policy_type,
            device_id=record.device_id, device_type=record.device_type, confidence=rule.confidence,
            description=f"{record.device_id} contacted {record.destination_type.value} destination ({record.dst_ip})",
            evidence={"destination_type": record.destination_type.value, "destination_ip": record.dst_ip, "blocked_destination_types": blocked, "protocol": record.protocol.value},
            record_id=record.record_id, timestamp=record.timestamp,
        )
    return None


def _check_traffic_ceiling(record: TelemetryRecord, rule: PolicyRule) -> Optional[PolicyViolation]:
    field = rule.parameters["field"]
    max_val = rule.parameters["max_value"]
    actual = getattr(record, field)
    if actual > max_val:
        return PolicyViolation(
            violation_id=str(uuid.uuid4()), rule_id=rule.rule_id, policy_type=rule.policy_type,
            device_id=record.device_id, device_type=record.device_type, confidence=rule.confidence,
            description=f"{record.device_id} {field} of {actual:,} exceeds limit of {max_val:,}",
            evidence={"field": field, "actual_value": actual, "max_allowed": max_val, "exceeded_by": actual - max_val, "protocol": record.protocol.value, "destination_ip": record.dst_ip},
            record_id=record.record_id, timestamp=record.timestamp,
        )
    return None


def _check_session_limit(record: TelemetryRecord, rule: PolicyRule) -> Optional[PolicyViolation]:
    max_dur = rule.parameters["max_duration"]
    if record.session_duration > max_dur:
        return PolicyViolation(
            violation_id=str(uuid.uuid4()), rule_id=rule.rule_id, policy_type=rule.policy_type,
            device_id=record.device_id, device_type=record.device_type, confidence=rule.confidence,
            description=f"{record.device_id} session of {record.session_duration}s exceeds {max_dur}s limit",
            evidence={"session_duration": record.session_duration, "max_allowed": max_dur, "protocol": record.protocol.value, "destination_ip": record.dst_ip},
            record_id=record.record_id, timestamp=record.timestamp,
        )
    return None


def _check_traffic_direction(record: TelemetryRecord, rule: PolicyRule) -> Optional[PolicyViolation]:
    if "max_inbound_ratio" in rule.parameters:
        ratio = record.bytes_received / record.bytes_sent if record.bytes_sent > 0 else 0.0
        if ratio > rule.parameters["max_inbound_ratio"]:
            return PolicyViolation(
                violation_id=str(uuid.uuid4()), rule_id=rule.rule_id, policy_type=rule.policy_type,
                device_id=record.device_id, device_type=record.device_type, confidence=rule.confidence,
                description=f"{record.device_id} receiving {ratio:.1f}x more than sending",
                evidence={"bytes_sent": record.bytes_sent, "bytes_received": record.bytes_received, "inbound_ratio": round(ratio, 4), "max_allowed_ratio": rule.parameters["max_inbound_ratio"]},
                record_id=record.record_id, timestamp=record.timestamp,
            )
    if "max_outbound_ratio" in rule.parameters:
        ratio = record.bytes_sent / record.bytes_received if record.bytes_received > 0 else float("inf")
        if ratio > rule.parameters["max_outbound_ratio"]:
            return PolicyViolation(
                violation_id=str(uuid.uuid4()), rule_id=rule.rule_id, policy_type=rule.policy_type,
                device_id=record.device_id, device_type=record.device_type, confidence=rule.confidence,
                description=f"{record.device_id} sending {ratio:.1f}x more than receiving",
                evidence={"bytes_sent": record.bytes_sent, "bytes_received": record.bytes_received, "outbound_ratio": round(ratio, 4), "max_allowed_ratio": rule.parameters["max_outbound_ratio"]},
                record_id=record.record_id, timestamp=record.timestamp,
            )
    return None


CHECKERS = {
    PolicyType.PROTOCOL_BLACKLIST: _check_protocol_blacklist,
    PolicyType.DESTINATION_RESTRICTION: _check_destination_restriction,
    PolicyType.TRAFFIC_CEILING: _check_traffic_ceiling,
    PolicyType.SESSION_LIMIT: _check_session_limit,
    PolicyType.TRAFFIC_DIRECTION: _check_traffic_direction,
}


class PolicyEngine:
    def __init__(self, rules: Optional[list[PolicyRule]] = None):
        self.rules = rules or POLICY_RULES
        self._rules_by_device: dict[DeviceType, list[PolicyRule]] = defaultdict(list)
        for rule in self.rules:
            self._rules_by_device[rule.device_type].append(rule)
        self.violations: list[PolicyViolation] = []
        self.device_states: dict[str, DevicePolicyState] = {}
        self.total_evaluated = 0

    def evaluate_record(self, record: TelemetryRecord) -> RecordEvaluation:
        device_rules = self._rules_by_device.get(record.device_type, [])
        record_violations = []
        for rule in device_rules:
            checker = CHECKERS.get(rule.policy_type)
            if not checker:
                continue
            violation = checker(record, rule)
            if violation:
                record_violations.append(violation)

        if record.device_id not in self.device_states:
            self.device_states[record.device_id] = DevicePolicyState(
                device_id=record.device_id, device_type=record.device_type,
                total_records_evaluated=0, total_violations=0,
                violations_by_type={}, violation_rate=0.0, is_compliant=True,
            )
        state = self.device_states[record.device_id]
        state.total_records_evaluated += 1
        self.total_evaluated += 1

        if record_violations:
            state.total_violations += len(record_violations)
            state.is_compliant = False
            state.last_violation = record.timestamp
            for v in record_violations:
                vtype = v.policy_type.value
                state.violations_by_type[vtype] = state.violations_by_type.get(vtype, 0) + 1
            self.violations.extend(record_violations)

        state.violation_rate = round(state.total_violations / max(state.total_records_evaluated, 1), 4)

        return RecordEvaluation(
            record_id=record.record_id, device_id=record.device_id,
            device_type=record.device_type, rules_checked=len(device_rules),
            violations_found=len(record_violations), violations=record_violations,
            is_compliant=len(record_violations) == 0,
        )

    def evaluate_records(self, records: list[TelemetryRecord]) -> list[RecordEvaluation]:
        return [self.evaluate_record(r) for r in records]

    def get_violations(self, device_id: Optional[str] = None, policy_type: Optional[PolicyType] = None, confidence: Optional[Confidence] = None) -> list[PolicyViolation]:
        results = self.violations
        if device_id:
            results = [v for v in results if v.device_id == device_id]
        if policy_type:
            results = [v for v in results if v.policy_type == policy_type]
        if confidence:
            results = [v for v in results if v.confidence == confidence]
        return results

    def get_device_state(self, device_id: str) -> Optional[DevicePolicyState]:
        return self.device_states.get(device_id)
