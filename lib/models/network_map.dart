/// Response from GET /network-map: nodes (devices) and edges (connections).
class NetworkMap {
  final List<NetworkMapNode> nodes;
  final List<NetworkMapEdge> edges;

  const NetworkMap({
    required this.nodes,
    required this.edges,
  });

  factory NetworkMap.fromJson(Map<String, dynamic> json) {
    final rawNodes = json['nodes'] as List<dynamic>? ?? [];
    final rawEdges = json['edges'] as List<dynamic>? ?? [];
    return NetworkMap(
      nodes: rawNodes
          .whereType<Map<String, dynamic>>()
          .map(NetworkMapNode.fromJson)
          .toList(),
      edges: rawEdges
          .whereType<Map<String, dynamic>>()
          .map(NetworkMapEdge.fromJson)
          .toList(),
    );
  }
}

class NetworkMapNode {
  final String id;
  final String name;
  final String deviceType;
  final String riskLevel;
  final int trustScore;
  final String status;

  const NetworkMapNode({
    required this.id,
    required this.name,
    required this.deviceType,
    required this.riskLevel,
    required this.trustScore,
    required this.status,
  });

  factory NetworkMapNode.fromJson(Map<String, dynamic> json) {
    return NetworkMapNode(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      deviceType: json['device_type'] as String? ?? '',
      riskLevel: (json['risk_level'] as String? ?? 'SAFE').toUpperCase(),
      trustScore: (json['trust_score'] as num? ?? 0).toInt(),
      status: json['status'] as String? ?? 'unknown',
    );
  }
}

class NetworkMapEdge {
  final String source;
  final String target;

  const NetworkMapEdge({
    required this.source,
    required this.target,
  });

  factory NetworkMapEdge.fromJson(Map<String, dynamic> json) {
    return NetworkMapEdge(
      source: json['source'] as String? ?? '',
      target: json['target'] as String? ?? '',
    );
  }
}
