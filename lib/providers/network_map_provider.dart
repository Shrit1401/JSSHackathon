import 'package:flutter/foundation.dart';
import '../models/network_map.dart';
import '../services/api_service.dart';

class NetworkMapProvider extends ChangeNotifier {
  NetworkMap? _networkMap;
  bool _isLoading = false;
  String? _error;

  NetworkMap? get networkMap => _networkMap;
  List<NetworkMapNode> get nodes => _networkMap?.nodes ?? [];
  List<NetworkMapEdge> get edges => _networkMap?.edges ?? [];
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> load() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _networkMap = await ApiService().fetchNetworkMap();
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
