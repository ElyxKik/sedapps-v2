import 'package:flutter_test/flutter_test.dart';
import 'package:sala_ai/src/features/cms/domain/cms_models.dart';

void main() {
  test('CmsArticle parses the backend contract', () {
    final article = CmsArticle.fromJson({
      'id': 'article-1',
      'slug': 'mon-article',
      'title': 'Mon article',
      'content_md': '# Contenu',
      'status': 'published',
      'reading_time_min': 3,
      'seo': {'title': 'SEO'},
    });
    expect(article.markdown, '# Contenu');
    expect(article.isPublished, isTrue);
    expect(article.readingTimeMinutes, 3);
  });

  test('CmsForm and submission preserve structured data', () {
    final form = CmsForm.fromJson({
      'id': 'form-1',
      'name': 'Contact',
      'schema': {'fields': []},
      'submission_count': 4,
    });
    final submission = FormSubmission.fromJson({
      'id': 'submission-1',
      'form_id': form.id,
      'form_name': form.name,
      'data': {'email': 'client@example.com'},
      'status': 'new',
    });
    expect(form.submissionCount, 4);
    expect(submission.data['email'], 'client@example.com');
  });

  test('CmsComment and media parse moderation and file metadata', () {
    final comment = CmsComment.fromJson({
      'id': 'comment-1',
      'article_id': 'article-1',
      'author_name': 'Alice',
      'author_email': 'alice@example.com',
      'content': 'Très bon article',
      'status': 'pending',
    });
    final media = CmsMedia.fromJson({
      'id': 'media-1',
      'filename': 'cover.png',
      'mime': 'image/png',
      'size_bytes': 2048,
      's3_key': 'project/cover.png',
      'width': 1200,
      'height': 630,
    });
    expect(comment.status, 'pending');
    expect(media.width, 1200);
    expect(media.sizeBytes, 2048);
  });

  test('CMS resources reject missing ids', () {
    expect(() => CmsArticle.fromJson({}), throwsA(isA<FormatException>()));
    expect(() => CmsForm.fromJson({}), throwsA(isA<FormatException>()));
    expect(() => CmsMedia.fromJson({}), throwsA(isA<FormatException>()));
  });
}
