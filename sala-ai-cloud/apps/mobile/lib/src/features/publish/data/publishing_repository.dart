import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/api_client.dart';
import '../domain/deployment.dart';

abstract interface class PublishingRepository {
  Future<Deployment> deploy(String projectId, {String? customDomain});
  Future<Deployment> status(String projectId, String deploymentId);
  Future<String> downloadUrl(String projectId);
}

final publishingRepositoryProvider = Provider<PublishingRepository>((ref) {
  return ApiPublishingRepository(ref.watch(apiClientProvider));
});

class ApiPublishingRepository implements PublishingRepository {
  const ApiPublishingRepository(this._api);

  final ApiClient _api;

  @override
  Future<Deployment> deploy(String projectId, {String? customDomain}) async {
    return Deployment.fromJson(
      await _api.deploySite(projectId, customDomain: customDomain),
    );
  }

  @override
  Future<Deployment> status(String projectId, String deploymentId) async {
    return Deployment.fromJson(await _api.deployment(projectId, deploymentId));
  }

  @override
  Future<String> downloadUrl(String projectId) =>
      _api.projectDownloadUrl(projectId);
}
