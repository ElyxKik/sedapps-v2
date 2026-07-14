enum DeploymentStatus {
  queued,
  building,
  uploading,
  success,
  failed,
  error,
  unknown;

  factory DeploymentStatus.parse(Object? value) {
    final normalized = value?.toString().toLowerCase();
    return values.firstWhere(
      (status) => status.name == normalized,
      orElse: () => DeploymentStatus.unknown,
    );
  }
}

class Deployment {
  const Deployment({
    required this.id,
    required this.status,
    this.domain,
    this.url,
    this.error,
  });

  factory Deployment.fromJson(Map<String, dynamic> json) {
    final id = (json['id'] ?? json['deployment_id'])?.toString() ?? '';
    if (id.isEmpty) {
      throw const FormatException('Déploiement invalide : id obligatoire.');
    }
    return Deployment(
      id: id,
      status: DeploymentStatus.parse(json['status']),
      domain: json['domain']?.toString(),
      url: json['url']?.toString(),
      error: json['error']?.toString(),
    );
  }

  final String id;
  final DeploymentStatus status;
  final String? domain;
  final String? url;
  final String? error;

  bool get isSuccessful => status == DeploymentStatus.success && url != null;
  bool get isFailed =>
      status == DeploymentStatus.failed || status == DeploymentStatus.error;
}
