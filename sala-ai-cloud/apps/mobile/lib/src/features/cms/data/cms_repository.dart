import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/api_client.dart';
import '../domain/cms_models.dart';

abstract interface class CmsRepository {
  Future<List<CmsArticle>> articles(String projectId);
  Future<CmsArticle> createArticle(
      String projectId, String title, String markdown, String status);
  Future<CmsArticle> updateArticle(String projectId, String articleId,
      {String? title, String? markdown, String? status});
  Future<void> deleteArticle(String projectId, String articleId);
  Future<List<CmsForm>> forms(String projectId);
  Future<List<FormSubmission>> submissions(String projectId);
  Future<List<CmsComment>> comments(String projectId);
  Future<void> updateCommentStatus(
      String projectId, String commentId, String status);
  Future<List<CmsMedia>> media(String projectId);
  Future<List<CmsPageEntry>> pages(String projectId);
}

final cmsRepositoryProvider = Provider<CmsRepository>(
    (ref) => ApiCmsRepository(ref.watch(apiClientProvider)));

final cmsArticlesProvider = FutureProvider.autoDispose
    .family<List<CmsArticle>, String>((ref, projectId) {
  return ref.watch(cmsRepositoryProvider).articles(projectId);
});

final cmsFormsProvider =
    FutureProvider.autoDispose.family<List<CmsForm>, String>((ref, projectId) {
  return ref.watch(cmsRepositoryProvider).forms(projectId);
});

final cmsSubmissionsProvider = FutureProvider.autoDispose
    .family<List<FormSubmission>, String>((ref, projectId) {
  return ref.watch(cmsRepositoryProvider).submissions(projectId);
});

final cmsCommentsProvider = FutureProvider.autoDispose
    .family<List<CmsComment>, String>((ref, projectId) {
  return ref.watch(cmsRepositoryProvider).comments(projectId);
});

final cmsMediaProvider =
    FutureProvider.autoDispose.family<List<CmsMedia>, String>((ref, projectId) {
  return ref.watch(cmsRepositoryProvider).media(projectId);
});

final cmsPagesProvider = FutureProvider.autoDispose
    .family<List<CmsPageEntry>, String>((ref, projectId) {
  return ref.watch(cmsRepositoryProvider).pages(projectId);
});

class ApiCmsRepository implements CmsRepository {
  const ApiCmsRepository(this._api);
  final ApiClient _api;

  List<T> _list<T>(List<dynamic> raw, T Function(Map<String, dynamic>) parse) =>
      raw
          .map((item) => parse(Map<String, dynamic>.from(item as Map)))
          .toList(growable: false);

  @override
  Future<List<CmsArticle>> articles(String projectId) async =>
      _list(await _api.articles(projectId), CmsArticle.fromJson);
  @override
  Future<CmsArticle> createArticle(String projectId, String title,
          String markdown, String status) async =>
      CmsArticle.fromJson(
          await _api.createArticle(projectId, title, markdown, status));
  @override
  Future<CmsArticle> updateArticle(String projectId, String articleId,
          {String? title, String? markdown, String? status}) async =>
      CmsArticle.fromJson(await _api.updateArticle(projectId, articleId,
          title: title, markdown: markdown, status: status));
  @override
  Future<void> deleteArticle(String projectId, String articleId) =>
      _api.deleteArticle(projectId, articleId);
  @override
  Future<List<CmsForm>> forms(String projectId) async =>
      _list(await _api.forms(projectId), CmsForm.fromJson);
  @override
  Future<List<FormSubmission>> submissions(String projectId) async =>
      _list(await _api.submissions(projectId), FormSubmission.fromJson);
  @override
  Future<List<CmsComment>> comments(String projectId) async =>
      _list(await _api.comments(projectId), CmsComment.fromJson);
  @override
  Future<void> updateCommentStatus(
          String projectId, String commentId, String status) =>
      _api.updateCommentStatus(projectId, commentId, status);
  @override
  Future<List<CmsMedia>> media(String projectId) async =>
      _list(await _api.media(projectId), CmsMedia.fromJson);

  @override
  Future<List<CmsPageEntry>> pages(String projectId) async {
    final response = await _api.projectDocument(projectId);
    final document = response['document'] as Map? ?? const {};
    final pages = document['pages'] as List? ?? const [];
    return pages
        .map((item) =>
            CmsPageEntry.fromJson(Map<String, dynamic>.from(item as Map)))
        .toList(growable: false);
  }
}
