import 'package:flutter_test/flutter_test.dart';
import 'package:sala_ai/src/features/projects/domain/project.dart';

void main() {
  test('Project parses a complete API response', () {
    final project = Project.fromJson({
      'id': 'project-1',
      'name': 'Mon site',
      'slug': 'mon-site',
      'status': 'published',
      'brief': {'tone': 'professional'},
      'design_tokens': {'primary': '#6366f1'},
      'active_job_id': 'job-1',
      'created_at': '2026-07-14T12:00:00Z',
    });

    expect(project.id, 'project-1');
    expect(project.status, ProjectStatus.published);
    expect(project.isPublished, isTrue);
    expect(project.previewNonce, 'mon-site');
    expect(project.createdAt, DateTime.utc(2026, 7, 14, 12));
    expect(project.defaultDomain, 'mon-site.salaai.site');
    expect(project.defaultUrl, 'https://mon-site.salaai.site');
  });

  test('Project rejects a response without identity', () {
    expect(
      () => Project.fromJson({'status': 'draft'}),
      throwsA(isA<FormatException>()),
    );
  });

  test('Project preserves an unknown server status safely', () {
    final project = Project.fromJson({
      'id': 'project-1',
      'name': 'Mon site',
      'slug': 'mon-site',
      'status': 'archived_in_future',
    });
    expect(project.status, ProjectStatus.unknown);
  });
}
