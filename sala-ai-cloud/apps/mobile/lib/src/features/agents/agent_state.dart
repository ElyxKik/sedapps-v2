import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/api_client.dart';
import 'agent_models.dart';

final currentJobIdProvider = StateProvider<String?>((ref) => null);
final currentJobProjectIdProvider = StateProvider<String?>((ref) => null);

/// Récupère les détails du projet associé au job actif si disponible.
final currentJobProjectProvider =
    FutureProvider<Map<String, dynamic>?>((ref) async {
  final projectId = ref.watch(currentJobProjectIdProvider);
  if (projectId == null || projectId.isEmpty) return null;
  final api = ref.watch(apiClientProvider);
  return api.project(projectId);
});

/// Stream le job courant en pollant toutes les 2s tant qu'il n'est pas terminé.
/// Permet d'afficher l'avancement des agents en temps réel dans le chat.
final currentJobProvider = StreamProvider<AiJobView?>((ref) async* {
  final jobId = ref.watch(currentJobIdProvider);
  if (jobId == null || jobId.isEmpty) {
    yield null;
    return;
  }
  final api = ref.watch(apiClientProvider);
  final currentJobId = ref.read(currentJobIdProvider.notifier);
  final currentJobProjectId = ref.read(currentJobProjectIdProvider.notifier);

  void _clearJob() {
    Timer(const Duration(seconds: 1), () {
      currentJobId.state = null;
      currentJobProjectId.state = null;
    });
  }

  while (true) {
    try {
      final data = await api.job(jobId);
      final job = AiJobView.fromJson(data);
      yield job;
      if (job.status == 'success' ||
          job.status == 'degraded' ||
          job.status == 'failed' ||
          job.status == 'error') {
        _clearJob();
        return;
      }
    } on DioException catch (e) {
      final statusCode = e.response?.statusCode;
      // Arrêt sur 404 (job introuvable) ou toute erreur 4xx non-transiente
      if (statusCode != null && statusCode >= 400 && statusCode < 500) {
        _clearJob();
        yield null;
        return;
      }
      // Erreur 5xx ou réseau : on log silencieusement et on réessaie
      yield null;
    } catch (_) {
      // Erreur inattendue : on laisse le prochain cycle réessayer
      yield null;
    }
    await Future<void>.delayed(const Duration(seconds: 2));
  }
});

