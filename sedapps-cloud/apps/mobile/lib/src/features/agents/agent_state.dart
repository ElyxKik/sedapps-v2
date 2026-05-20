import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/api_client.dart';
import 'agent_models.dart';

final currentJobIdProvider = StateProvider<String?>((ref) => null);

/// Stream le job courant en pollant toutes les 2s tant qu'il n'est pas terminé.
/// Permet d'afficher l'avancement des agents en temps réel dans le chat.
final currentJobProvider = StreamProvider<AiJobView?>((ref) async* {
  final jobId = ref.watch(currentJobIdProvider);
  if (jobId == null || jobId.isEmpty) {
    yield null;
    return;
  }
  final api = ref.watch(apiClientProvider);
  while (true) {
    try {
      final data = await api.job(jobId);
      final job = AiJobView.fromJson(data);
      yield job;
      if (job.status == 'success' || job.status == 'failed' || job.status == 'error') {
        return;
      }
    } catch (_) {
      yield null;
    }
    await Future<void>.delayed(const Duration(seconds: 2));
  }
});
