import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/device.dart';
import '../services/api_service.dart';
import '../config/app_config.dart';

class DevicesProvider extends ChangeNotifier {
  List<Device> _devices = [];
  bool _isLoading = false;
  String? _error;
  Timer? _timer;

  List<Device> get devices => _devices;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> load() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _devices = await ApiService().fetchDevices();
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
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
