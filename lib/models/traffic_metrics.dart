class TrafficMetrics {
  final double currentIn;
  final double currentOut;
  final double baselineIn;
  final double baselineOut;
  final double packetLoss;

  TrafficMetrics({
    required this.currentIn,
    required this.currentOut,
    required this.baselineIn,
    required this.baselineOut,
    required this.packetLoss,
  });

  /// Build from a device's traffic_rate (real API — no dedicated /traffic endpoint)
  factory TrafficMetrics.fromDevice(double trafficRate) {
    // Split traffic_rate roughly 60/40 inbound/outbound
    final currentIn = trafficRate * 0.6;
    final currentOut = trafficRate * 0.4;
    // Baseline is ~30% of current (if anomalous) or equal
    final baseline = trafficRate > 10 ? trafficRate * 0.3 : trafficRate;
    return TrafficMetrics(
      currentIn: currentIn,
      currentOut: currentOut,
      baselineIn: baseline * 0.6,
      baselineOut: baseline * 0.4,
      packetLoss: trafficRate > 30 ? 2.5 : trafficRate > 10 ? 0.5 : 0.0,
    );
  }

  factory TrafficMetrics.fromJson(Map<String, dynamic> json) {
    return TrafficMetrics(
      currentIn: (json['current_in'] as num).toDouble(),
      currentOut: (json['current_out'] as num).toDouble(),
      baselineIn: (json['baseline_in'] as num).toDouble(),
      baselineOut: (json['baseline_out'] as num).toDouble(),
      packetLoss: (json['packet_loss'] as num).toDouble(),
    );
  }
}
