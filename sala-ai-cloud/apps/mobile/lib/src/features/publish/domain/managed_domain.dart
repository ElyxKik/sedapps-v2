class ManagedDomain {
  const ManagedDomain({
    required this.id,
    required this.name,
    required this.provider,
    required this.status,
    this.expiresAt,
    this.parentDomainId,
    this.projectId,
    this.verificationName,
    this.verificationValue,
  });

  final String id;
  final String name;
  final String provider;
  final String status;
  final DateTime? expiresAt;
  final String? parentDomainId;
  final String? projectId;
  final String? verificationName;
  final String? verificationValue;

  bool get isSubdomain => parentDomainId != null;
  bool get isAvailableForProject => projectId == null;

  factory ManagedDomain.fromJson(Map<String, dynamic> json) => ManagedDomain(
        id: json['id'].toString(),
        name: json['name'].toString(),
        provider: json['provider']?.toString() ?? 'external',
        status: json['status']?.toString() ?? 'active',
        expiresAt: json['expires_at'] == null
            ? null
            : DateTime.tryParse(json['expires_at'].toString()),
        parentDomainId: json['parent_domain_id']?.toString(),
        projectId: json['project_id']?.toString(),
        verificationName: json['verification_name']?.toString(),
        verificationValue: json['verification_value']?.toString(),
      );
}

class DomainSearchResult {
  const DomainSearchResult({
    required this.domain,
    required this.available,
    required this.checked,
    required this.message,
  });
  final String domain;
  final bool available;
  final bool checked;
  final String message;

  factory DomainSearchResult.fromJson(Map<String, dynamic> json) =>
      DomainSearchResult(
        domain: json['domain'].toString(),
        available: json['available'] == true,
        checked: json['checked'] == true,
        message: json['message']?.toString() ?? '',
      );
}
