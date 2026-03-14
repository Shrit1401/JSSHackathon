import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:http/io_client.dart';
import '../config/app_config.dart';
import '../models/device.dart';
import '../models/alert.dart';
import '../models/overview_stats.dart';
import '../models/traffic_metrics.dart';
import '../models/network_map.dart';
import 'mock_data.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  static http.Client _createClient() {
    final httpClient = HttpClient()
      ..connectionTimeout = const Duration(seconds: 30)
      ..idleTimeout = const Duration(seconds: 30);
    return IOClient(httpClient);
  }

  late final http.Client _client = _createClient();

  static const Duration _timeout = Duration(seconds: 25);
  static const Map<String, String> _headers = {
    'Accept': 'application/json',
    'User-Agent': 'JSS-Mobile/1.0 (Flutter)',
  };

  Uri _uri(String path, [Map<String, String>? queryParams]) {
    final uri = Uri.parse('${AppConfig.baseUrl}$path');
    return queryParams != null && queryParams.isNotEmpty
        ? uri.replace(queryParameters: queryParams)
        : uri;
  }

  Future<Map<String, dynamic>> _get(String path, [Map<String, String>? queryParams]) async {
    final uri = _uri(path, queryParams);
    final response = await _client.get(uri, headers: _headers).timeout(_timeout);
    if (response.statusCode != 200) throw Exception('HTTP ${response.statusCode}');
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<dynamic>> _getList(String path, [Map<String, String>? queryParams]) async {
    final uri = _uri(path, queryParams);
    final response = await _client.get(uri, headers: _headers).timeout(_timeout);
    if (response.statusCode != 200) throw Exception('HTTP ${response.statusCode}');
    return jsonDecode(response.body) as List<dynamic>;
  }

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body) async {
    final uri = _uri(path);
    final headers = {..._headers, 'Content-Type': 'application/json'};
    final response = await _client
        .post(uri, headers: headers, body: jsonEncode(body))
        .timeout(_timeout);
    if (response.statusCode != 200 && response.statusCode != 201) {
      throw Exception('HTTP ${response.statusCode}');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  // ── Health ────────────────────────────────────────────────────────────────

  /// GET /health — liveness check. Returns true if status == "ok".
  Future<bool> checkHealth() async {
    try {
      final data = await _get('/health');
      return data['status'] == 'ok';
    } catch (_) {
      return false;
    }
  }

  // ── Overview (GET /overview + GET /events; fallback to mock on failure) ─────

  Future<OverviewStats> fetchOverview() async {
    try {
      final overviewJson = await _get('/overview');
      List<Map<String, dynamic>> events = [];
      try {
        final raw = await _getList('/events', {'limit': '10'});
        events = raw.whereType<Map<String, dynamic>>().toList();
      } catch (_) {}
      return OverviewStats.fromApi(overviewJson, events);
    } catch (_) {
      return OverviewStats.fromJson(MockData.overview());
    }
  }

  // ── Devices (GET /devices, GET /devices/{id}; fallback to mock on failure) ───

  Future<List<Device>> fetchDevices() async {
    try {
      final list = await _getList('/devices');
      return list
          .whereType<Map<String, dynamic>>()
          .map((d) => Device.fromJson(d))
          .toList();
    } catch (e) {
      return MockData.devices().map(Device.fromJson).toList();
    }
  }

  Future<Device> fetchDeviceById(String id) async {
    try {
      final data = await _get('/devices/$id');
      return Device.fromJson(data);
    } catch (e) {
      debugPrint('[ApiService] fetchDeviceById($id) failed: $e');
      return Device.fromJson(MockData.deviceById(id));
    }
  }

  /// No dedicated traffic endpoint; derive from features if available, else zeroed.
  Future<TrafficMetrics> fetchDeviceTraffic(String id) async {
    try {
      final list = await _getList('/features/device/$id');
      if (list.isNotEmpty && list.first is Map<String, dynamic>) {
        final f = list.first as Map<String, dynamic>;
        final sent = (f['total_bytes_sent'] as num? ?? 0).toDouble();
        final recv = (f['total_bytes_received'] as num? ?? 0).toDouble();
        final rate = (sent + recv) / (1024 * 1024); // MB
        return TrafficMetrics.fromDevice(rate.clamp(0.0, 500.0));
      }
    } catch (_) {}
    return TrafficMetrics.fromDevice(0.0);
  }

  /// GET /devices/{id}/explain — plain English explanation of risk level.
  Future<String> fetchDeviceExplanation(String id) async {
    try {
      final data = await _get('/devices/$id/explain');
      final explanation = data['explanation'] as String?;
      if (explanation != null && explanation.isNotEmpty) return explanation;
      return '';
    } catch (e) {
      debugPrint('[ApiService] fetchDeviceExplanation($id) failed: $e');
      return MockData.deviceExplanation(id)['explanation'] as String;
    }
  }

  // ── Network map (topology) ────────────────────────────────────────────────

  /// GET /network-map — nodes (devices) and edges for graph.
  Future<NetworkMap> fetchNetworkMap() async {
    try {
      final data = await _get('/network-map');
      return NetworkMap.fromJson(data);
    } catch (e) {
      debugPrint('[ApiService] fetchNetworkMap failed: $e');
      return const NetworkMap(nodes: [], edges: []);
    }
  }

  // ── Events ────────────────────────────────────────────────────────────────

  Future<List<Map<String, dynamic>>> fetchEvents([Map<String, String>? params]) async {
    try {
      final q = params ?? {'limit': '100'};
      final list = await _getList('/events', q);
      return list.whereType<Map<String, dynamic>>().toList();
    } catch (e) {
      debugPrint('[ApiService] fetchEvents failed: $e');
      return [];
    }
  }

  // ── Alerts ────────────────────────────────────────────────────────────────

  Future<List<Alert>> fetchAlerts([Map<String, String>? params]) async {
    final q = params ?? {'limit': '100'};
    const retryStatuses = {404, 502, 503}; // cold start / temporary

    for (var attempt = 0; attempt < 2; attempt++) {
      try {
        final raw = await _client.get(_uri('/alerts', q), headers: _headers).timeout(_timeout);
        if (raw.statusCode == 200) {
          final decoded = jsonDecode(raw.body);
          List<dynamic> list;
          if (decoded is List) {
            list = decoded;
          } else if (decoded is Map<String, dynamic>) {
            final maybe = decoded['alerts'] ?? decoded['data'] ?? decoded['items'];
            list = maybe is List ? maybe : <dynamic>[];
          } else {
            list = <dynamic>[];
          }
          final alerts = <Alert>[];
          for (final e in list) {
            if (e is! Map<String, dynamic>) continue;
            Map<String, dynamic> map = e;
            if (map.length == 1) {
              final inner = map.values.single;
              if (inner is Map<String, dynamic>) map = inner;
            }
            try {
              alerts.add(Alert.fromJson(map));
            } catch (_) {}
          }
          return alerts;
        }
        if (attempt == 0 && retryStatuses.contains(raw.statusCode)) {
          await Future<void>.delayed(const Duration(seconds: 2));
          continue;
        }
      } catch (e) {
        debugPrint('[ApiService] fetchAlerts attempt ${attempt + 1} failed: $e');
        if (attempt == 0) {
          await Future<void>.delayed(const Duration(seconds: 2));
          continue;
        }
      }
    }
    debugPrint('[ApiService] fetchAlerts using mock data');
    return MockData.alerts().map(Alert.fromJson).toList();
  }

  Future<void> acknowledgeAlert(String alertId) async {
    try {
      await _post('/alerts/acknowledge/$alertId', {});
    } catch (e) {
      debugPrint('[ApiService] acknowledgeAlert failed (non-fatal): $e');
      rethrow;
    }
  }

  // ── Simulation (Supabase-synced) ──────────────────────────────────────────

  /// POST /simulate-attack — attack_type optional (random if omitted).
  Future<Map<String, dynamic>> simulateAttack({
    required String deviceId,
    String? attackType,
  }) async {
    final body = <String, dynamic>{'device_id': deviceId};
    if (attackType != null && attackType.isNotEmpty) {
      body['attack_type'] = attackType;
    }
    return _post('/simulate-attack', body);
  }

  // ── Assistant (Hack Club AI) ──────────────────────────────────────────────

  Future<String> sendAssistantMessage(String text) async {
    try {
      final uri = Uri.parse('${AppConfig.hackClubAiBaseUrl}/chat/completions');
      final headers = {
        'Authorization': 'Bearer ${AppConfig.hackClubAiApiKey}',
        'Content-Type': 'application/json',
        ..._headers,
      };
      final body = {
        'model': 'qwen/qwen3-32b',
        'messages': [
          {'role': 'system', 'content': _assistantSystemPrompt},
          {'role': 'user', 'content': text},
        ],
      };
      final response = await _client
          .post(uri, headers: headers, body: jsonEncode(body))
          .timeout(_timeout);
      if (response.statusCode != 200) {
        throw Exception('AI API HTTP ${response.statusCode}');
      }
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final choices = data['choices'] as List<dynamic>?;
      final content = choices?.isNotEmpty == true
          ? (choices!.first as Map<String, dynamic>)['message']
                as Map<String, dynamic>?
          : null;
      final reply = content?['content'] as String?;
      if (reply != null && reply.isNotEmpty) return reply.trim();
      throw Exception('Empty AI response');
    } catch (e) {
      debugPrint('[ApiService] sendAssistantMessage failed: $e');
      return MockData.assistantReply(text)['reply'] as String;
    }
  }

  static const String _assistantSystemPrompt =
      'You are an IoT security assistant. The user is managing a network of devices (routers, cameras, sensors, NAS, etc.). '
      'Help them understand device risks, trust scores, alerts, and recommend remediation. Keep answers concise and actionable.';
}
