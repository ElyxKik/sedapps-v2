enum ArticleStatus {
  draft,
  published,
  scheduled,
  archived,
  unknown;

  factory ArticleStatus.parse(Object? value) => values.firstWhere(
        (status) => status.name == value?.toString().toLowerCase(),
        orElse: () => ArticleStatus.unknown,
      );
}

class CmsArticle {
  const CmsArticle({
    required this.id,
    required this.slug,
    required this.title,
    required this.markdown,
    required this.status,
    required this.readingTimeMinutes,
    required this.seo,
    this.excerpt,
    this.coverUrl,
    this.publishedAt,
    this.scheduledAt,
  });

  factory CmsArticle.fromJson(Map<String, dynamic> json) {
    final id = json['id']?.toString() ?? '';
    if (id.isEmpty) throw const FormatException('Article sans identifiant.');
    return CmsArticle(
      id: id,
      slug: json['slug']?.toString() ?? '',
      title: json['title']?.toString() ?? 'Article sans titre',
      markdown: json['content_md']?.toString() ?? '',
      status: ArticleStatus.parse(json['status']),
      readingTimeMinutes: (json['reading_time_min'] as num?)?.toInt() ?? 0,
      seo: Map<String, dynamic>.from(json['seo'] as Map? ?? const {}),
      excerpt: json['excerpt']?.toString(),
      coverUrl: json['cover_url']?.toString(),
      publishedAt: _date(json['published_at']),
      scheduledAt: _date(json['scheduled_at']),
    );
  }

  final String id;
  final String slug;
  final String title;
  final String markdown;
  final ArticleStatus status;
  final int readingTimeMinutes;
  final Map<String, dynamic> seo;
  final String? excerpt;
  final String? coverUrl;
  final DateTime? publishedAt;
  final DateTime? scheduledAt;

  bool get isPublished => status == ArticleStatus.published;
}

class CmsForm {
  const CmsForm(
      {required this.id,
      required this.name,
      required this.schema,
      required this.submissionCount,
      this.createdAt});
  factory CmsForm.fromJson(Map<String, dynamic> json) => CmsForm(
        id: _requiredId(json, 'Formulaire'),
        name: json['name']?.toString() ?? 'Formulaire',
        schema: Map<String, dynamic>.from(json['schema'] as Map? ?? const {}),
        submissionCount: (json['submission_count'] as num?)?.toInt() ?? 0,
        createdAt: _date(json['created_at']),
      );
  final String id;
  final String name;
  final Map<String, dynamic> schema;
  final int submissionCount;
  final DateTime? createdAt;
}

class FormSubmission {
  const FormSubmission(
      {required this.id,
      required this.formId,
      required this.formName,
      required this.data,
      required this.status,
      this.createdAt});
  factory FormSubmission.fromJson(Map<String, dynamic> json) => FormSubmission(
        id: _requiredId(json, 'Soumission'),
        formId: json['form_id']?.toString() ?? '',
        formName: json['form_name']?.toString() ?? 'Message',
        data: Map<String, dynamic>.from(json['data'] as Map? ?? const {}),
        status: json['status']?.toString() ?? 'new',
        createdAt: _date(json['created_at']),
      );
  final String id;
  final String formId;
  final String formName;
  final Map<String, dynamic> data;
  final String status;
  final DateTime? createdAt;
}

class CmsComment {
  const CmsComment(
      {required this.id,
      required this.articleId,
      required this.authorName,
      required this.authorEmail,
      required this.content,
      required this.status,
      this.createdAt});
  factory CmsComment.fromJson(Map<String, dynamic> json) => CmsComment(
        id: _requiredId(json, 'Commentaire'),
        articleId: json['article_id']?.toString() ?? '',
        authorName: json['author_name']?.toString() ?? 'Visiteur',
        authorEmail: json['author_email']?.toString() ?? '',
        content: json['content']?.toString() ?? '',
        status: json['status']?.toString() ?? 'pending',
        createdAt: _date(json['created_at']),
      );
  final String id;
  final String articleId;
  final String authorName;
  final String authorEmail;
  final String content;
  final String status;
  final DateTime? createdAt;
}

class CmsMedia {
  const CmsMedia(
      {required this.id,
      required this.filename,
      required this.mime,
      required this.sizeBytes,
      required this.s3Key,
      this.width,
      this.height,
      this.alt,
      this.folder,
      this.createdAt});
  factory CmsMedia.fromJson(Map<String, dynamic> json) => CmsMedia(
        id: _requiredId(json, 'Média'),
        filename: json['filename']?.toString() ?? 'Fichier',
        mime: json['mime']?.toString() ?? 'application/octet-stream',
        sizeBytes: (json['size_bytes'] as num?)?.toInt() ?? 0,
        s3Key: json['s3_key']?.toString() ?? '',
        width: (json['width'] as num?)?.toInt(),
        height: (json['height'] as num?)?.toInt(),
        alt: json['alt']?.toString(),
        folder: json['folder']?.toString(),
        createdAt: _date(json['created_at']),
      );
  final String id;
  final String filename;
  final String mime;
  final int sizeBytes;
  final String s3Key;
  final int? width;
  final int? height;
  final String? alt;
  final String? folder;
  final DateTime? createdAt;
}

class CmsPageEntry {
  const CmsPageEntry(
      {required this.id, required this.type, required this.slug});

  factory CmsPageEntry.fromJson(Map<String, dynamic> json) => CmsPageEntry(
        id: _requiredId(json, 'Page'),
        type: json['type']?.toString() ?? 'Page',
        slug: (json['props'] as Map?)?['slug']?.toString() ??
            json['id']?.toString() ??
            'page',
      );

  final String id;
  final String type;
  final String slug;
}

DateTime? _date(Object? value) => DateTime.tryParse(value?.toString() ?? '');

String _requiredId(Map<String, dynamic> json, String resource) {
  final id = json['id']?.toString() ?? '';
  if (id.isEmpty) throw FormatException('$resource sans identifiant.');
  return id;
}
