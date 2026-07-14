enum ProjectStatus {
  draft,
  generating,
  ready,
  published,
  failed,
  unknown;

  factory ProjectStatus.parse(Object? value) {
    final normalized = value?.toString().toLowerCase();
    return values.firstWhere(
      (status) => status.name == normalized,
      orElse: () => ProjectStatus.unknown,
    );
  }
}

class Project {
  const Project({
    required this.id,
    required this.name,
    required this.slug,
    required this.status,
    required this.brief,
    required this.designTokens,
    this.sector,
    this.customDomain,
    this.previewNonce,
    this.activeJobId,
    this.createdAt,
    this.defaultDomain,
    this.defaultUrl,
  });

  factory Project.fromJson(Map<String, dynamic> json) {
    final id = json['id']?.toString() ?? '';
    final name = json['name']?.toString().trim() ?? '';
    if (id.isEmpty || name.isEmpty) {
      throw const FormatException('Projet invalide : id et nom obligatoires.');
    }
    final slug = json['slug']?.toString() ?? '';
    return Project(
      id: id,
      name: name,
      slug: slug,
      sector: json['sector']?.toString(),
      status: ProjectStatus.parse(json['status']),
      brief: Map<String, dynamic>.from(json['brief'] as Map? ?? const {}),
      designTokens:
          Map<String, dynamic>.from(json['design_tokens'] as Map? ?? const {}),
      customDomain: json['custom_domain']?.toString(),
      previewNonce:
          json['preview_nonce']?.toString() ?? (slug.isEmpty ? null : slug),
      activeJobId: json['active_job_id']?.toString(),
      createdAt: DateTime.tryParse(json['created_at']?.toString() ?? ''),
      defaultDomain: json['default_domain']?.toString() ??
          (slug.isEmpty ? null : '$slug.salaai.site'),
      defaultUrl: json['default_url']?.toString() ??
          (slug.isEmpty ? null : 'https://$slug.salaai.site'),
    );
  }

  final String id;
  final String name;
  final String slug;
  final String? sector;
  final ProjectStatus status;
  final Map<String, dynamic> brief;
  final Map<String, dynamic> designTokens;
  final String? customDomain;
  final String? previewNonce;
  final String? activeJobId;
  final DateTime? createdAt;
  final String? defaultDomain;
  final String? defaultUrl;

  bool get isPublished => status == ProjectStatus.published;
  bool get isGenerating => status == ProjectStatus.generating;

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'slug': slug,
        'sector': sector,
        'status': status.name,
        'brief': brief,
        'design_tokens': designTokens,
        'custom_domain': customDomain,
        'preview_nonce': previewNonce,
        'active_job_id': activeJobId,
        'created_at': createdAt?.toIso8601String(),
        'default_domain': defaultDomain,
        'default_url': defaultUrl,
      };
}
