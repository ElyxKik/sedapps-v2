import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../widgets/page_scaffold.dart';
import 'agent_state.dart';
import 'agent_timeline.dart';

class AgentsPage extends ConsumerWidget {
  const AgentsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final jobId = ref.watch(currentJobIdProvider);
    return PageScaffold(
      title: 'Étapes de création',
      action: OutlinedButton.icon(
        onPressed:
            jobId == null ? null : () => ref.invalidate(currentJobProvider),
        icon: const Icon(Icons.refresh),
        label: const Text('Rafraîchir'),
      ),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Création en cours',
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                Text(jobId == null
                    ? 'Aucune création en cours. Crée un site pour voir les étapes se dérouler en direct.'
                    : jobId),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),
        ref.watch(currentJobProvider).when(
              data: (job) => AgentTimeline(job: job),
              loading: () => const Card(
                  child: Padding(
                      padding: EdgeInsets.all(20),
                      child: LinearProgressIndicator())),
              error: (error, stackTrace) => Card(
                  child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Text('Les étapes ne sont pas disponibles pour le moment.')),
            ),
      ],
    );
  }
}
