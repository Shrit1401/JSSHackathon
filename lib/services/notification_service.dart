import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import '../config/app_router.dart';
import '../screens/devices/device_detail_screen.dart';
import 'api_service.dart';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final _plugin = FlutterLocalNotificationsPlugin();
  Timer? _healthTimer;
  bool? _lastHealthy;

  Future<void> initialize() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    const settings = InitializationSettings(android: androidSettings, iOS: iosSettings);

    await _plugin.initialize(
      settings,
      onDidReceiveNotificationResponse: _onNotificationTap,
    );
  }

  void _onNotificationTap(NotificationResponse response) {
    final deviceId = response.payload;
    if (deviceId != null && deviceId.isNotEmpty) {
      AppRouter.navigatorKey.currentState?.push(
        MaterialPageRoute(
          builder: (_) => DeviceDetailScreen(deviceId: deviceId),
        ),
      );
    }
  }

  Future<void> showAlert({
    required String title,
    required String body,
    required String deviceId,
  }) async {
    const androidDetails = AndroidNotificationDetails(
      'iot_alerts',
      'IoT Alerts',
      channelDescription: 'Real-time IoT security alerts',
      importance: Importance.high,
      priority: Priority.high,
      color: Color(0xFF00E5FF),
    );
    const iosDetails = DarwinNotificationDetails();
    const details = NotificationDetails(android: androidDetails, iOS: iosDetails);

    await _plugin.show(
      deviceId.hashCode,
      title,
      body,
      details,
      payload: deviceId,
    );
  }

  /// Push notification when API/system goes down (called by health monitor).
  Future<void> showSystemDown() async {
    const androidDetails = AndroidNotificationDetails(
      'system_status',
      'System Status',
      channelDescription: 'Sentinel system and API status',
      importance: Importance.high,
      priority: Priority.high,
      color: Color(0xFFFF3D3D),
    );
    const iosDetails = DarwinNotificationDetails();
    const details = NotificationDetails(android: androidDetails, iOS: iosDetails);

    await _plugin.show(
      'system_down'.hashCode,
      'Sentinel — System down',
      'API unreachable. Check connection or backend.',
      details,
    );
  }

  /// Start background health checks; notifies once when system goes from up to down.
  void startHealthMonitor() {
    _healthTimer?.cancel();
    _healthTimer = Timer.periodic(const Duration(seconds: 30), (_) => _checkHealthAndNotify());
  }

  Future<void> _checkHealthAndNotify() async {
    try {
      final healthy = await ApiService().checkHealth();
      if (_lastHealthy == true && !healthy) {
        await showSystemDown();
      }
      _lastHealthy = healthy;
    } catch (_) {
      if (_lastHealthy != false) {
        await showSystemDown();
      }
      _lastHealthy = false;
    }
  }

  void stopHealthMonitor() {
    _healthTimer?.cancel();
    _healthTimer = null;
    _lastHealthy = null;
  }
}
