import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/api_client.dart';
import '../domain/project.dart';

abstract interface class ProjectRepository {
  Future<List<Project>> list();
  Future<Project> get(String id);
  Future<void> delete(String id);
}

final projectRepositoryProvider = Provider<ProjectRepository>((ref) {
  return ApiProjectRepository(ref.watch(apiClientProvider));
});

class ApiProjectRepository implements ProjectRepository {
  const ApiProjectRepository(this._api);

  final ApiClient _api;

  @override
  Future<List<Project>> list() async {
    final response = await _api.projects();
    return response
        .map((item) => Project.fromJson(Map<String, dynamic>.from(item as Map)))
        .toList(growable: false);
  }

  @override
  Future<Project> get(String id) async =>
      Project.fromJson(await _api.project(id));

  @override
  Future<void> delete(String id) => _api.deleteProject(id);
}

final projectsProvider = FutureProvider<List<Project>>((ref) {
  return ref.watch(projectRepositoryProvider).list();
});
