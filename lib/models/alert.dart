enum AlertSeverity { info, low, medium, high, critical }

class Alert {
  final String id;
  final String deviceId;
  final String deviceName;
  final String alertType;
  final AlertSeverity severity;
  final String message;
  final DateTime timestamp;
  final bool acknowledged;

  Alert({
    required this.id,
    required this.deviceId,
    required this.deviceName,
    required this.alertType,
    required this.severity,
    required this.message,
    required this.timestamp,
    this.acknowledged = false,
  });

  static String _str(dynamic v) => v?.toString().trim() ?? '';

  factory Alert.fromJson(Map<String, dynamic> json) {
    final sevStr = _str(json['severity']).toUpperCase();
    final sev = switch (sevStr.isEmpty ? 'LOW' : sevStr) {
      'CRITICAL' => AlertSeverity.critical,
      'HIGH' => AlertSeverity.high,
      'MEDIUM' => AlertSeverity.medium,
      'INFO' => AlertSeverity.info,
      _ => AlertSeverity.low,
    };

    final id = _str(json['alert_id']).isEmpty ? _str(json['id']) : _str(json['alert_id']);
    final deviceId = _str(json['device_id']);
    final deviceName = _str(json['device_name']).isEmpty ? deviceId : _str(json['device_name']);
    final alertType = _str(json['alert_type']).isEmpty
        ? (_str(json['title']).isEmpty ? 'Alert' : _str(json['title']))
        : _str(json['alert_type']);
    final message = _str(json['reason']).isEmpty
        ? (_str(json['message']).isEmpty
            ? (_str(json['title']).isEmpty ? _str(json['description']) : _str(json['title']))
            : _str(json['message']))
        : _str(json['reason']);
    final ts = DateTime.tryParse(_str(json['timestamp']));
    final acknowledged = json['acknowledged'] == true;

    return Alert(
      id: id.isEmpty ? DateTime.now().millisecondsSinceEpoch.toString() : id,
      deviceId: deviceId,
      deviceName: deviceName,
      alertType: alertType.isEmpty ? 'Alert' : alertType,
      severity: sev,
      message: message.isEmpty ? 'No details' : message,
      timestamp: ts ?? DateTime.now(),
      acknowledged: acknowledged,
    );
  }
}
