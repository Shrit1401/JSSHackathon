class MockData {
  static Map<String, dynamic> overview() => {
    'total_devices': 6,
    'safe': 3,
    'low': 1,
    'medium': 1,
    'high': 1,
    'online': 5,
    'offline': 1,
    'recent_activity': [
      {
        'icon': 'warning',
        'description': 'Suspicious port scan detected on NAS-Server',
        'timestamp': '2026-03-13T10:45:00Z',
      },
      {
        'icon': 'shield',
        'description': 'Security policy updated on Router-Main',
        'timestamp': '2026-03-13T10:30:00Z',
      },
      {
        'icon': 'device',
        'description': 'New device joined network: SmartTV-Living',
        'timestamp': '2026-03-13T10:15:00Z',
      },
      {
        'icon': 'alert',
        'description': 'High traffic anomaly on IP Camera-01',
        'timestamp': '2026-03-13T09:55:00Z',
      },
      {
        'icon': 'check',
        'description': 'Laptop-Dev passed security scan',
        'timestamp': '2026-03-13T09:30:00Z',
      },
    ],
  };

  static List<Map<String, dynamic>> devices() => [
    {
      'id': 'dev-001',
      'name': 'Router-Main',
      'device_type': 'router',
      'ip_address': '192.168.1.1',
      'vendor': 'Cisco Systems',
      'trust_score': 91.0,
      'risk_level': 'SAFE',
      'traffic_rate': 5.2,
      'status': 'online',
      'open_ports': [22, 80, 443, 8080],
      'protocol_usage': {'HTTP': 0.3, 'HTTPS': 0.6, 'SSH': 0.1},
      'security_explanation':
          'Router operating normally. All security policies applied.',
      'last_seen': '2026-03-13T10:45:00Z',
    },
    {
      'id': 'dev-002',
      'name': 'Laptop-Dev',
      'device_type': 'laptop',
      'ip_address': '192.168.1.45',
      'vendor': 'Apple Inc.',
      'trust_score': 85.0,
      'risk_level': 'SAFE',
      'traffic_rate': 3.1,
      'status': 'online',
      'open_ports': [22, 5900],
      'protocol_usage': {'HTTPS': 0.8, 'SSH': 0.2},
      'security_explanation':
          'Developer laptop with standard ports. Last security scan passed.',
      'last_seen': '2026-03-13T10:44:00Z',
    },
    {
      'id': 'dev-003',
      'name': 'SmartTV-Living',
      'device_type': 'smart_tv',
      'ip_address': '192.168.1.72',
      'vendor': 'Samsung Electronics',
      'trust_score': 78.0,
      'risk_level': 'SAFE',
      'traffic_rate': 7.4,
      'status': 'online',
      'open_ports': [80, 443, 8080, 9197],
      'protocol_usage': {'HTTP': 0.4, 'HTTPS': 0.5, 'OTHER': 0.1},
      'security_explanation':
          'Smart TV showing slightly elevated outbound connections.',
      'last_seen': '2026-03-13T10:40:00Z',
    },
    {
      'id': 'dev-004',
      'name': 'IP Camera-01',
      'device_type': 'camera',
      'ip_address': '192.168.1.110',
      'vendor': 'Hikvision',
      'trust_score': 48.0,
      'risk_level': 'MEDIUM',
      'traffic_rate': 18.3,
      'status': 'online',
      'open_ports': [23, 80, 554, 8000, 8200],
      'protocol_usage': {'RTSP': 0.7, 'HTTP': 0.2, 'TELNET': 0.1},
      'security_explanation':
          'IP Camera using outdated firmware. Telnet port 23 is open — critical risk.',
      'last_seen': '2026-03-13T10:38:00Z',
    },
    {
      'id': 'dev-005',
      'name': 'NAS-Server',
      'device_type': 'hub',
      'ip_address': '192.168.1.130',
      'vendor': 'Synology',
      'trust_score': 41.0,
      'risk_level': 'HIGH',
      'traffic_rate': 24.6,
      'status': 'online',
      'open_ports': [21, 22, 80, 443, 445, 5000, 5001],
      'protocol_usage': {'FTP': 0.3, 'SMB': 0.4, 'HTTPS': 0.3},
      'security_explanation':
          'NAS device exposed to port scan. FTP port 21 active without encryption.',
      'last_seen': '2026-03-13T10:35:00Z',
    },
    {
      'id': 'dev-006',
      'name': 'IoT-Sensor-03',
      'device_type': 'sensor',
      'ip_address': '192.168.1.205',
      'vendor': 'Unknown',
      'trust_score': 18.0,
      'risk_level': 'HIGH',
      'traffic_rate': 55.9,
      'status': 'compromised',
      'open_ports': [23, 80, 1900, 7547, 8443],
      'protocol_usage': {'HTTP': 0.1, 'UNKNOWN': 0.9},
      'security_explanation':
          'IoT sensor exhibiting botnet-like behavior. Massive outbound traffic anomaly. Isolate immediately.',
      'last_seen': '2026-03-13T10:42:00Z',
    },
  ];

  static Map<String, dynamic> deviceById(String id) {
    return devices().firstWhere(
      (d) => d['id'] == id,
      orElse: () => devices().first,
    );
  }

  static Map<String, dynamic> trafficMetrics(String deviceId) {
    final scores = {
      'dev-001': {'ci': 3.1, 'co': 2.1, 'bi': 3.0, 'bo': 2.0, 'pl': 0.1},
      'dev-002': {'ci': 1.9, 'co': 1.2, 'bi': 2.0, 'bo': 1.5, 'pl': 0.0},
      'dev-003': {'ci': 4.5, 'co': 2.9, 'bi': 3.5, 'bo': 2.5, 'pl': 0.2},
      'dev-004': {'ci': 11.0, 'co': 7.3, 'bi': 4.0, 'bo': 2.0, 'pl': 1.8},
      'dev-005': {'ci': 14.8, 'co': 9.8, 'bi': 5.0, 'bo': 3.0, 'pl': 3.2},
      'dev-006': {'ci': 33.5, 'co': 22.4, 'bi': 2.0, 'bo': 1.0, 'pl': 8.5},
    };
    final m = scores[deviceId] ?? scores['dev-001']!;
    return {
      'current_in': m['ci'],
      'current_out': m['co'],
      'baseline_in': m['bi'],
      'baseline_out': m['bo'],
      'packet_loss': m['pl'],
    };
  }

  static Map<String, dynamic> deviceExplanation(String deviceId) {
    final explanations = {
      'dev-001':
          'Router operating normally. All security policies applied. Firmware is up to date.',
      'dev-002':
          'Developer laptop with standard ports. Last security scan passed all checks.',
      'dev-003':
          'Smart TV showing slightly elevated outbound connections to advertising networks.',
      'dev-004':
          'IP Camera using outdated firmware with known CVEs. Telnet port 23 is open — critical risk.',
      'dev-005':
          'NAS device exposed to port scan from external IPs. FTP port 21 active without encryption.',
      'dev-006':
          'IoT sensor exhibiting botnet-like behavior. Massive outbound traffic anomaly. Isolate immediately.',
    };
    return {
      'explanation': explanations[deviceId] ?? 'No security data available.',
    };
  }

  static List<Map<String, dynamic>> alerts() => [
    {
      'id': 'alert-001',
      'alert_type': 'PORT_SCAN',
      'device_name': 'NAS-Server',
      'device_id': 'dev-005',
      'severity': 'HIGH',
      'message':
          'External IP 203.0.113.42 performed sequential port scan across 512 ports.',
      'timestamp': '2026-03-13T10:45:00Z',
    },
    {
      'id': 'alert-002',
      'alert_type': 'TRAFFIC_SPIKE',
      'device_name': 'IoT-Sensor-03',
      'device_id': 'dev-006',
      'severity': 'HIGH',
      'message':
          'Outbound traffic 12x above baseline. Possible C2 communication detected.',
      'timestamp': '2026-03-13T10:32:00Z',
    },
    {
      'id': 'alert-003',
      'alert_type': 'DATA_EXFILTRATION',
      'device_name': 'IoT-Sensor-03',
      'device_id': 'dev-006',
      'severity': 'CRITICAL',
      'message':
          'Trust score dropped to 18. Device behavior matches known botnet signatures.',
      'timestamp': '2026-03-13T10:20:00Z',
    },
    {
      'id': 'alert-004',
      'alert_type': 'POLICY_VIOLATION',
      'device_name': 'IP Camera-01',
      'device_id': 'dev-004',
      'severity': 'MEDIUM',
      'message':
          'Telnet (port 23) is open. Unencrypted protocol poses credential theft risk.',
      'timestamp': '2026-03-13T09:55:00Z',
    },
    {
      'id': 'alert-005',
      'alert_type': 'POLICY_VIOLATION',
      'device_name': 'NAS-Server',
      'device_id': 'dev-005',
      'severity': 'MEDIUM',
      'message':
          'FTP (port 21) active without TLS. All file transfers are unencrypted.',
      'timestamp': '2026-03-13T09:15:00Z',
    },
  ];

  static Map<String, dynamic> assistantReply(String message) {
    final lower = message.toLowerCase();
    if (lower.contains('compromised') || lower.contains('sensor')) {
      return {
        'reply':
            'IoT-Sensor-03 (192.168.1.205) is showing critical compromise indicators: outbound traffic 12x baseline, trust score 18/100, behavior matching known botnet patterns. Immediate action: isolate the device, capture traffic logs, and factory reset after identifying the attack vector.',
      };
    } else if (lower.contains('camera') || lower.contains('telnet')) {
      return {
        'reply':
            'IP Camera-01 has port 23 (Telnet) open — a major security risk as Telnet transmits data unencrypted. Steps: (1) Disable Telnet in camera settings, (2) Update firmware via manufacturer portal, (3) Change default credentials.',
      };
    } else if (lower.contains('risk') || lower.contains('score')) {
      return {
        'reply':
            'Main risk contributors: IoT-Sensor-03 (score 18, likely compromised), NAS-Server (score 41, active port scan target), IP Camera-01 (score 48, open Telnet). Addressing these 3 devices could significantly improve your network trust score.',
      };
    } else if (lower.contains('nas') || lower.contains('ftp')) {
      return {
        'reply':
            'NAS-Server has FTP (port 21) enabled without encryption — credentials and data are visible in plaintext. Fix: disable FTP in Synology DSM and enable SFTP or FTPS instead.',
      };
    } else {
      return {
        'reply':
            'Security assistant online. I can analyze device risks, explain alerts, and recommend remediation. Try: "What should I do about the compromised sensor?", "Why is my NAS flagged?", or "Which devices are safe?"',
      };
    }
  }
}
