import 'dart:math' as math;

import 'package:flutter/material.dart';
import '../../models/device.dart';
import '../../models/traffic_metrics.dart';
import '../../services/api_service.dart';
import '../../theme/app_theme.dart';
import '../../widgets/simple_line_chart.dart';

class DeviceDetailScreen extends StatefulWidget {
  final String deviceId;
  /// When provided, stats show immediately from this device (no loading). API still refreshes in background.
  final Device? device;

  const DeviceDetailScreen({super.key, required this.deviceId, this.device});

  @override
  State<DeviceDetailScreen> createState() => _DeviceDetailScreenState();
}

class _DeviceDetailScreenState extends State<DeviceDetailScreen> {
  Device? _device;
  TrafficMetrics? _traffic;
  String? _lastEventDescription;
  String? _explanationOverride;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    // Show stats immediately when we have the device from the list
    if (widget.device != null) {
      _device = widget.device;
      _traffic = TrafficMetrics.fromDevice(widget.device!.trafficRate);
      _isLoading = false;
    }
    _loadData();
  }

  Future<void> _loadData() async {
    // If we already have device (passed from list), don't show loading — refresh in background
    final showLoading = _device == null;
    if (showLoading) {
      setState(() {
        _isLoading = true;
        _error = null;
      });
    }
    try {
      final api = ApiService();
      final device = await api.fetchDeviceById(widget.deviceId);
      final traffic = await api.fetchDeviceTraffic(widget.deviceId);
      if (!mounted) return;
      setState(() {
        _device = device;
        _traffic = traffic;
        _isLoading = false;
      });
      if (device.securityExplanation.isEmpty) {
        api.fetchDeviceExplanation(widget.deviceId).then((explanation) {
          if (!mounted) return;
          setState(() => _explanationOverride = explanation.isNotEmpty ? explanation : null);
        });
      }
      api.fetchEvents({'limit': '50'}).then((events) {
        if (!mounted) return;
        final deviceEvents = events
            .where((e) => e['device_id'] == widget.deviceId)
            .toList();
        deviceEvents.sort((a, b) {
          final ta = a['timestamp'] as String? ?? '';
          final tb = b['timestamp'] as String? ?? '';
          return tb.compareTo(ta);
        });
        final lastEvent = deviceEvents.isNotEmpty ? deviceEvents.first : null;
        final lastEventDesc = lastEvent?['description'] as String? ??
            lastEvent?['message'] as String? ??
            (deviceEvents.isEmpty ? null : 'Event recorded');
        setState(() => _lastEventDescription = lastEventDesc);
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          // Only show error if we had no data (e.g. opened from notification with only id)
          if (_device == null) _error = e.toString();
        });
      }
    }
  }

  Color get _riskColor => switch (_device?.riskLevel) {
        RiskLevel.safe => AppColors.safe,
        RiskLevel.low => AppColors.warning,
        RiskLevel.medium => AppColors.warning,
        RiskLevel.high => AppColors.danger,
        RiskLevel.compromised => AppColors.danger,
        _ => AppColors.textSecondary,
      };

  void _pop() {
    if (!mounted) return;
    Navigator.of(context).pop();
  }

  /// Full stats body matching the reference: header, metric cards, trust/traffic
  /// history charts, open ports, protocol usage, security explanation.
  Widget _buildStatsBody() {
    final d = _device!;
    final t = _traffic!;
    final trust = d.trustScore.isNaN ? 0.0 : d.trustScore;
    final riskLabel = switch (d.riskLevel) {
      RiskLevel.safe => 'Safe',
      RiskLevel.low => 'Low',
      RiskLevel.medium => 'Medium',
      RiskLevel.high => 'High',
      RiskLevel.compromised => 'Compromised',
    };
    final trustHistory = _simulateHistory(trust, 24, 0.92, 1.08);
    final trafficRate = t.currentIn + t.currentOut;
    final trafficHistory = _simulateHistory(trafficRate, 24, 0.85, 1.15);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // Header: device type + status badge
        Text(
          _deviceTypeLabel(d.type),
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 13,
          ),
        ),
        const SizedBox(height: 6),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: _riskColor.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: _riskColor.withValues(alpha: 0.4)),
          ),
          child: Text(
            riskLabel,
            style: TextStyle(
              color: _riskColor,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        const SizedBox(height: 20),
        // Trust history (graphs first)
        _buildSectionTitle('Trust history'),
        const SizedBox(height: 10),
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.surfaceBorder),
          ),
          child: SimpleLineChart(
            values: trustHistory,
            lineColor: Theme.of(context).colorScheme.primary,
            height: 100,
          ),
        ),
        const SizedBox(height: 20),
        // Traffic history
        _buildSectionTitle('Traffic history'),
        const SizedBox(height: 10),
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.surfaceBorder),
          ),
          child: SimpleLineChart(
            values: trafficHistory,
            lineColor: AppColors.textPrimary.withValues(alpha: 0.85),
            height: 100,
          ),
        ),
        const SizedBox(height: 24),
        // Stats cards below both graphs
        _buildOverviewCards(),
        const SizedBox(height: 20),
        // Open ports
        _buildSectionTitle('Open ports'),
        const SizedBox(height: 10),
        _buildOpenPortsSection(),
        const SizedBox(height: 20),
        // Protocol usage
        _buildSectionTitle('Protocol usage'),
        const SizedBox(height: 10),
        _buildProtocolSection(context),
        const SizedBox(height: 20),
        // Security explanation
        _buildSectionTitle('Security explanation'),
        const SizedBox(height: 10),
        _buildExplanationSection(),
        const SizedBox(height: 48),
      ],
    );
  }

  static List<double> _simulateHistory(double center, int points, double minFactor, double maxFactor) {
    final r = math.Random(42);
    return List.generate(points, (i) {
      final noise = (r.nextDouble() * 2 - 1) * 0.08;
      final trend = 0.02 * math.sin(i * 0.3);
      final f = (center + noise * center + trend * center).clamp(
        center * minFactor,
        center * maxFactor,
      );
      return f;
    });
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        color: AppColors.textPrimary,
        fontSize: 14,
        fontWeight: FontWeight.w600,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final canShowContent = !_isLoading && _error == null && _device != null && _traffic != null;
    final primary = Theme.of(context).colorScheme.primary;

    return PopScope(
      canPop: true,
      onPopInvokedWithResult: (didPop, result) {
        if (didPop) return;
        _pop();
      },
      child: Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        leadingWidth: 56,
        leading: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: _pop,
            child: const Padding(
              padding: EdgeInsets.all(16),
              child: Icon(Icons.arrow_back_rounded, color: AppColors.textPrimary, size: 24),
            ),
          ),
        ),
          title: Text(
            _device?.name ?? widget.deviceId,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
            ),
          ),
          actions: [
            TextButton(
              onPressed: _pop,
              child: const Text(
                'Close',
                style: TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 13,
                ),
              ),
            ),
          ],
          bottom: PreferredSize(
            preferredSize: const Size.fromHeight(1),
            child: Container(height: 1, color: AppColors.surfaceBorder),
          ),
        ),
        body: _isLoading
            ? Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const _PulseLoader(),
                    const SizedBox(height: 16),
                    const Text(
                      'Loading…',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              )
            : _error != null
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text('ERR',
                            style: TextStyle(
                                color: AppColors.danger,
                                fontSize: 32,
                                fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        Text(_error!,
                            style: const TextStyle(
                                color: AppColors.textSecondary, fontSize: 12)),
                        const SizedBox(height: 16),
                        GestureDetector(
                          onTap: _loadData,
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 16, vertical: 8),
                            decoration: BoxDecoration(
                              border: Border.all(color: primary),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text('RETRY',
                                style: TextStyle(
                                    color: primary,
                                    fontSize: 12,
                                    letterSpacing: 1)),
                          ),
                        ),
                      ],
                    ),
                  )
                : !canShowContent
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Text('No data',
                                style: TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 16)),
                            const SizedBox(height: 16),
                            TextButton(
                              onPressed: _loadData,
                              child: const Text('Retry'),
                            ),
                            const SizedBox(height: 24),
                            TextButton(
                              onPressed: _pop,
                              child: const Text('Go back'),
                            ),
                          ],
                        ),
                      )
                    : ColoredBox(
                        color: AppColors.background,
                        child: RefreshIndicator(
                          onRefresh: _loadData,
                          color: Theme.of(context).colorScheme.primary,
                          backgroundColor: AppColors.surface,
                          child: SingleChildScrollView(
                            physics: const AlwaysScrollableScrollPhysics(),
                            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                            child: ConstrainedBox(
                              constraints: BoxConstraints(
                                minHeight: MediaQuery.of(context).size.height - 200,
                              ),
                              child: _buildStatsBody(),
                            ),
                          ),
                        ),
                      ),
      ),
    );
  }

  /// Two cards: Trust score + Last event (from backend).
  Widget _buildOverviewCards() {
    final device = _device!;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.surfaceBorder),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Trust score',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11,
                    letterSpacing: 0.5,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  '${(device.trustScore.isNaN ? 0.0 : device.trustScore).toStringAsFixed(0)}%',
                  style: TextStyle(
                    color: _riskColor,
                    fontSize: 26,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Updated on simulation events',
                  style: TextStyle(
                    color: AppColors.textSecondary.withValues(alpha: 0.8),
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.surfaceBorder),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Last event',
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11,
                    letterSpacing: 0.5,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  _lastEventDescription ?? 'No recent anomalies',
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 12,
                    height: 1.3,
                  ),
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 6),
                Text(
                  'Telemetry + detections',
                  style: TextStyle(
                    color: AppColors.textSecondary.withValues(alpha: 0.8),
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  static String _deviceTypeLabel(String type) {
    const labels = {
      'router': 'Gateway / NAT',
      'gateway': 'Gateway / NAT',
      'camera': 'Security Camera',
      'smart_tv': 'Media Device',
      'laptop': 'Workstation',
      'sensor': 'ENV Sensor',
      'hub': 'Video Recorder / Hub',
      'printer': 'Network Printer',
      'thermostat': 'HVAC Control',
      'smartphone': 'Mobile Device',
    };
    return labels[type.toLowerCase()] ?? type;
  }

  static const Map<int, String> _portLabels = {
    21: 'FTP',
    22: 'SSH',
    23: 'Telnet',
    80: 'HTTP',
    443: 'HTTPS',
    554: 'RTSP',
    445: 'SMB',
    8080: 'HTTP',
    8000: 'HTTP',
    8200: 'HTTP',
    8443: 'HTTPS',
    1900: 'UPnP',
    7547: 'TR-069',
    5000: 'UPnP',
    5001: 'Synology',
    5900: 'VNC',
  };

  Widget _buildOpenPortsSection() {
    final device = _device!;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.surfaceBorder),
      ),
      child: device.openPorts.isEmpty
          ? Text(
              'No open ports',
              style: TextStyle(
                color: AppColors.textSecondary.withValues(alpha: 0.8),
                fontSize: 12,
              ),
            )
          : Wrap(
              spacing: 8,
              runSpacing: 8,
              children: device.openPorts.map((port) {
                final label = _portLabels[port] ?? '';
                final display = label.isEmpty ? port.toString() : '$port/$label';
                final isDangerous = [21, 23, 445, 1900, 7547].contains(port);
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: isDangerous
                        ? AppColors.danger.withValues(alpha: 0.1)
                        : AppColors.surfaceLight,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: isDangerous
                          ? AppColors.danger.withValues(alpha: 0.35)
                          : AppColors.surfaceBorder,
                    ),
                  ),
                  child: Text(
                    display,
                    style: TextStyle(
                      color: isDangerous
                          ? AppColors.danger
                          : AppColors.textSecondary,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                );
              }).toList(),
            ),
    );
  }

  Widget _buildExplanationSection() {
    final explanation = _explanationOverride ?? _device!.securityExplanation;
    if (explanation.isEmpty) return const SizedBox.shrink();

    return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(8),
            border:
                Border.all(color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.2)),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 2,
                height: double.infinity,
                constraints: const BoxConstraints(minHeight: 40),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primary,
                  borderRadius: BorderRadius.circular(1),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  explanation,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                    height: 1.6,
                  ),
                ),
              ),
            ],
          ),
        );
  }

  Widget _buildProtocolSection(BuildContext context) {
    final protocols = _device!.protocolUsage.entries.toList()
      ..sort((a, b) {
        final va = a.value.isNaN ? 0.0 : a.value;
        final vb = b.value.isNaN ? 0.0 : b.value;
        return vb.compareTo(va);
      });

    return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: AppColors.surfaceBorder),
          ),
          child: Column(
            children: protocols.map((entry) {
              final value = entry.value;
              final safeValue = value.isNaN ? 0.0 : value;
              final pct = (safeValue * 100).toStringAsFixed(0);
              final progress = safeValue.clamp(0.0, 1.0);
              return Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          entry.key,
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 11,
                            letterSpacing: 0.5,
                          ),
                        ),
                        Text(
                          '$pct%',
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.primary,
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    SizedBox(
                      width: double.infinity,
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(2),
                        child: Stack(
                          children: [
                            Container(height: 4, color: AppColors.surfaceBorder),
                            LayoutBuilder(
                              builder: (context, c) => SizedBox(
                                width: c.maxWidth * progress,
                                height: 4,
                                child: Container(
                                  height: 4,
                                  color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.7),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        );
  }
}

class _PulseLoader extends StatefulWidget {
  const _PulseLoader();

  @override
  State<_PulseLoader> createState() => _PulseLoaderState();
}

class _PulseLoaderState extends State<_PulseLoader>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 800))
      ..repeat();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, __) => Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(3, (i) {
          final delay = i * 0.33;
          final opacity =
              (((_ctrl.value + delay) % 1.0) < 0.5) ? 1.0 : 0.2;
          return Container(
            margin: const EdgeInsets.symmetric(horizontal: 3),
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Theme.of(context).colorScheme.primary.withValues(alpha: opacity),
            ),
          );
        }),
      ),
    );
  }
}
