import 'package:flutter/material.dart';

class ActivityItem {
  final IconData icon;
  final String description;
  final DateTime timestamp;

  ActivityItem({
    required this.icon,
    required this.description,
    required this.timestamp,
  });

  /// Build from a real API event object (GET /events)
  factory ActivityItem.fromEvent(Map<String, dynamic> json) {
    final eventType = (json['event_type'] as String? ?? '').toUpperCase();
    final icon = switch (eventType) {
      final t when t.contains('SPIKE') || t.contains('FLOOD') =>
        Icons.trending_up,
      final t when t.contains('EXFIL') => Icons.output_rounded,
      final t when t.contains('BACKDOOR') => Icons.pest_control,
      final t when t.contains('VIOLATION') => Icons.gpp_bad_outlined,
      final t when t.contains('DESTINATION') => Icons.alt_route,
      final t when t.contains('FLUCTUATION') => Icons.swap_vert,
      _ => Icons.info_outline,
    };

    return ActivityItem(
      icon: icon,
      description: json['description'] as String? ?? eventType,
      timestamp:
          DateTime.tryParse(json['timestamp'] as String? ?? '') ??
          DateTime.now(),
    );
  }

  /// Fallback: build from legacy mock format
  factory ActivityItem.fromJson(Map<String, dynamic> json) {
    final iconMap = <String, IconData>{
      'warning': Icons.warning_amber_rounded,
      'shield': Icons.shield_outlined,
      'device': Icons.devices,
      'network': Icons.network_check,
      'alert': Icons.notifications_active,
      'check': Icons.check_circle_outline,
    };

    return ActivityItem(
      icon: iconMap[json['icon'] as String? ?? ''] ?? Icons.info_outline,
      description: json['description'] as String? ?? '',
      timestamp:
          DateTime.tryParse(json['timestamp'] as String? ?? '') ??
          DateTime.now(),
    );
  }
}

class OverviewStats {
  final int totalDevices;
  final int safeDevices; // safe count
  final int lowDevices; // low risk
  final int mediumDevices; // medium risk
  final int highDevices; // high risk
  final int onlineDevices;
  final int offlineDevices;
  final List<ActivityItem> recentActivity;

  OverviewStats({
    required this.totalDevices,
    required this.safeDevices,
    required this.lowDevices,
    required this.mediumDevices,
    required this.highDevices,
    required this.onlineDevices,
    required this.offlineDevices,
    required this.recentActivity,
  });

  // Derived: suspicious = low + medium, critical = high
  int get suspiciousDevices => lowDevices + mediumDevices;
  int get highRiskDevices => highDevices;

  // Derived trust score: weighted average of safe/low/medium/high
  double get networkTrustScore {
    if (totalDevices == 0) return 100.0;
    final weighted =
        (safeDevices * 95.0) +
        (lowDevices * 70.0) +
        (mediumDevices * 45.0) +
        (highDevices * 15.0);
    return (weighted / totalDevices).clamp(0.0, 100.0);
  }

  /// From GET /trust/summary + GET /events (new API; no /overview).
  factory OverviewStats.fromTrustAndEvents(
    Map<String, dynamic> trustSummary,
    List<Map<String, dynamic>> events,
  ) {
    final byRisk = trustSummary['devices_by_risk'] is Map<String, dynamic>
        ? trustSummary['devices_by_risk'] as Map<String, dynamic>
        : <String, dynamic>{};
    final safe = (byRisk['SAFE'] as num? ?? 0).toInt();
    final low = (byRisk['LOW'] as num? ?? 0).toInt();
    final medium = (byRisk['MEDIUM'] as num? ?? 0).toInt();
    final high = (byRisk['HIGH'] as num? ?? 0).toInt();
    final total = (trustSummary['total_devices'] as num? ?? 0).toInt();
    final activity = events.take(5).map(ActivityItem.fromEvent).toList();

    return OverviewStats(
      totalDevices: total,
      safeDevices: safe,
      lowDevices: low,
      mediumDevices: medium,
      highDevices: high,
      onlineDevices: total,
      offlineDevices: 0,
      recentActivity: activity,
    );
  }

  factory OverviewStats.fromApi(
    Map<String, dynamic> overviewJson,
    List<Map<String, dynamic>> events,
  ) {
    final activity = events.take(5).map(ActivityItem.fromEvent).toList();

    return OverviewStats(
      totalDevices: (overviewJson['total_devices'] as num? ?? 0).toInt(),
      safeDevices: (overviewJson['safe'] as num? ?? 0).toInt(),
      lowDevices: (overviewJson['low'] as num? ?? 0).toInt(),
      mediumDevices: (overviewJson['medium'] as num? ?? 0).toInt(),
      highDevices: (overviewJson['high'] as num? ?? 0).toInt(),
      onlineDevices: (overviewJson['online'] as num? ?? 0).toInt(),
      offlineDevices: (overviewJson['offline'] as num? ?? 0).toInt(),
      recentActivity: activity,
    );
  }

  /// Legacy mock fallback
  factory OverviewStats.fromJson(Map<String, dynamic> json) {
    final activity = (json['recent_activity'] as List? ?? [])
        .map((e) => ActivityItem.fromJson(e as Map<String, dynamic>))
        .toList();

    return OverviewStats(
      totalDevices: (json['total_devices'] as num? ?? 0).toInt(),
      safeDevices: (json['safe_devices'] as num? ?? json['safe'] as num? ?? 0)
          .toInt(),
      lowDevices: (json['low'] as num? ?? 0).toInt(),
      mediumDevices: (json['medium'] as num? ?? 0).toInt(),
      highDevices:
          (json['high_risk_devices'] as num? ?? json['high'] as num? ?? 0)
              .toInt(),
      onlineDevices: (json['online'] as num? ?? 0).toInt(),
      offlineDevices: (json['offline'] as num? ?? 0).toInt(),
      recentActivity: activity,
    );
  }
}
