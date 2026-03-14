import 'dart:async';
import 'package:flutter/material.dart';
import '../models/overview_stats.dart';
import '../services/api_service.dart';
import '../config/app_config.dart';

class OverviewProvider extends ChangeNotifier {
  OverviewStats? _stats;
  bool _isLoading = false;
  String? _error;
  Timer? _timer;

  OverviewStats? get stats => _stats;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> load() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _stats = await ApiService().fetchOverview();
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
    _timer = Timer.periodic(Duration(seconds: AppConfig.refreshIntervalSeconds), (_) => load());
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
