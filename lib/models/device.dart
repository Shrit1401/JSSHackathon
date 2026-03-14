enum RiskLevel { safe, low, medium, high, compromised }

class Device {
  final String id;
  final String name;
  final String type; // device_type
  final String ip; // ip_address
  final String vendor;
  final double trustScore; // trust_score
  final RiskLevel riskLevel;
  final double trafficRate; // traffic_rate MB/s
  final String status; // online / offline / compromised
  final List<int> openPorts;
  final Map<String, double> protocolUsage;
  final String securityExplanation;
  final DateTime? lastSeen;

  Device({
    required this.id,
    required this.name,
    required this.type,
    required this.ip,
    required this.vendor,
    required this.trustScore,
    required this.riskLevel,
    required this.trafficRate,
    required this.status,
    required this.openPorts,
    required this.protocolUsage,
    required this.securityExplanation,
    this.lastSeen,
  });

  /// From API DeviceState + optional DeviceTrustScore (telemetry/devices + trust/scores).
  factory Device.fromDeviceStateAndTrust(
    Map<String, dynamic> state,
    Map<String, dynamic>? trust,
  ) {
    final id = state['device_id'] as String? ?? state['id'] as String? ?? '';
    final riskStr = (trust?['risk_level'] as String? ?? state['risk_level'] as String? ?? 'SAFE').toUpperCase();
    final risk = switch (riskStr) {
      'LOW' => RiskLevel.low,
      'MED' => RiskLevel.medium,
      'MEDIUM' => RiskLevel.medium,
      'HIGH' => RiskLevel.high,
      'COMPROMISED' => RiskLevel.compromised,
      _ => RiskLevel.safe,
    };
    final trustScore = (trust?['trust_score'] as num? ?? state['trust_score'] as num? ?? 0).toDouble();
    final isCompromised = state['is_compromised'] as bool? ?? false;
    final activeAttack = state['active_attack'] as String?;
    final status = activeAttack != null
        ? 'compromised'
        : isCompromised
            ? 'compromised'
            : (state['last_seen'] != null ? 'online' : 'unknown');

    return Device(
      id: id,
      name: state['name'] as String? ?? id,
      type: state['device_type'] as String? ?? state['type'] as String? ?? '',
      ip: state['ip_address'] as String? ?? state['ip'] as String? ?? '',
      vendor: state['vendor'] as String? ?? '',
      trustScore: trustScore,
      riskLevel: risk,
      trafficRate: (state['traffic_rate'] as num? ?? 0).toDouble(),
      status: status,
      openPorts: state['open_ports'] is List
          ? (state['open_ports'] as List)
              .map((p) => int.tryParse(p.toString().split('/').first) ?? 0)
              .where((p) => p > 0)
              .toList()
          : [],
      protocolUsage: state['protocol_usage'] is Map<String, dynamic>
          ? (state['protocol_usage'] as Map<String, dynamic>).map(
              (k, v) => MapEntry(k, (v is num ? v.toDouble() : 0.0)),
            )
          : <String, double>{},
      securityExplanation: state['security_explanation'] as String? ?? '',
      lastSeen: state['last_seen'] != null
          ? DateTime.tryParse(state['last_seen'] as String)
          : null,
    );
  }

  factory Device.fromJson(Map<String, dynamic> json) {
    final riskStr = (json['risk_level'] as String? ?? 'SAFE').toUpperCase();
    final risk = switch (riskStr) {
      'LOW' => RiskLevel.low,
      'MED' => RiskLevel.medium,
      'MEDIUM' => RiskLevel.medium,
      'HIGH' => RiskLevel.high,
      'COMPROMISED' => RiskLevel.compromised,
      _ => RiskLevel.safe,
    };

    final rawPorts = json['open_ports'] is List ? json['open_ports'] as List : const [];
    final ports = rawPorts
        .map((p) {
          final s = p.toString();
          final portStr = s.contains('/') ? s.split('/').first : s;
          return int.tryParse(portStr) ?? 0;
        })
        .where((p) => p > 0)
        .toList();

    final rawProtocol = json['protocol_usage'] is Map<String, dynamic>
        ? json['protocol_usage'] as Map<String, dynamic>
        : <String, dynamic>{};
    final protocol = rawProtocol.map(
      (k, v) => MapEntry(k, (v is num ? v.toDouble() : 0.0)),
    );

    return Device(
      id: json['id'] as String? ?? json['device_id'] as String? ?? '',
      name: json['name'] as String? ?? json['device_id'] as String? ?? json['id'] as String? ?? '',
      type: json['device_type'] as String? ?? json['type'] as String? ?? '',
      ip: json['ip_address'] as String? ?? json['ip'] as String? ?? '',
      vendor: json['vendor'] as String? ?? '',
      trustScore: (json['trust_score'] as num? ?? 0).toDouble(),
      riskLevel: risk,
      trafficRate: (json['traffic_rate'] as num? ?? 0).toDouble(),
      status: json['status'] as String? ?? 'unknown',
      openPorts: ports,
      protocolUsage: protocol,
      securityExplanation: json['security_explanation'] as String? ?? '',
      lastSeen: json['last_seen'] != null
          ? DateTime.tryParse(json['last_seen'] as String)
          : null,
    );
  }
}
