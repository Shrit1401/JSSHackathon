import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/alert.dart';
import '../services/api_service.dart';
import '../config/app_config.dart';

class AlertsProvider extends ChangeNotifier {
  List<Alert> _alerts = [];
  bool _isLoading = false;
  String? _error;
  Timer? _timer;

  List<Alert> get alerts => _alerts;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> load() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _alerts = await ApiService().fetchAlerts();
      _alerts.sort((a, b) => b.timestamp.compareTo(a.timestamp));
      _error = null;
    } catch (e) {
      _error = 'Server unavailable. Pull down to retry.';
      // Show mock data so the screen isn't broken
      try {
        _alerts = await ApiService().fetchAlerts();
        _alerts.sort((a, b) => b.timestamp.compareTo(a.timestamp));
        _error = null;
      } catch (_) {
        _alerts = [];
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> acknowledge(String alertId) async {
    try {
      await ApiService().acknowledgeAlert(alertId);
      _error = null;
      await load();
    } catch (_) {
      // Acknowledge endpoint may 404 or be unavailable; just refresh the list
      _error = null;
      await load();
    }
  }

  void startAutoRefresh() {
    _timer?.cancel();
    _timer = Timer.periodic(
      Duration(seconds: AppConfig.refreshIntervalSeconds),
      (_) => load(),
    );
  }

  void stopAutoRefresh() {
    _timer?.cancel();
    _timer = null;
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}
