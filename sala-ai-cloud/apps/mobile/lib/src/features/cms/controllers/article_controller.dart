import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/cms_repository.dart';
import '../domain/cms_models.dart';

final cmsArticleControllerProvider = Provider<CmsArticleController>((ref) {
  return CmsArticleController(ref);
});

class CmsArticleController {
  const CmsArticleController(this._ref);
  final Ref _ref;

  Future<CmsArticle> create(String projectId) async {
    final article = await _ref.read(cmsRepositoryProvider).createArticle(
          projectId,
          'Nouvel article',
          '# Nouvel article\n\nCommence à écrire ici.',
          'draft',
        );
    _ref.invalidate(cmsArticlesProvider(projectId));
    return article;
  }

  Future<CmsArticle> save(
    String projectId,
    String articleId, {
    required String title,
    required String markdown,
    required String status,
  }) async {
    final article = await _ref.read(cmsRepositoryProvider).updateArticle(
          projectId,
          articleId,
          title: title,
          markdown: markdown,
          status: status,
        );
    _ref.invalidate(cmsArticlesProvider(projectId));
    return article;
  }

  Future<void> delete(String projectId, String articleId) async {
    await _ref.read(cmsRepositoryProvider).deleteArticle(projectId, articleId);
    _ref.invalidate(cmsArticlesProvider(projectId));
  }
}
