import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/services.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../../widgets/notifications.dart';
import '../../widgets/page_scaffold.dart';
import '../projects/project_workspace_state.dart';

class PublishPage extends ConsumerWidget {
  const PublishPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final workspace = ref.watch(projectWorkspaceProvider);
    final publish = workspace.publish;
    final isPublishing =
        publish.status == 'building' || publish.status == 'uploading';
    final projectId = ref.watch(currentProjectIdProvider);
    return PageScaffold(
      title: 'Mettre en ligne',
      action: Wrap(
        spacing: 10,
        children: [
          OutlinedButton.icon(
            onPressed: projectId == null
                ? null
                : () async {
                    try {
                      final url = await ref
                          .read(apiClientProvider)
                          .projectDownloadUrl(projectId);
                      final launched = await launchUrl(Uri.parse(url),
                          mode: LaunchMode.externalApplication);
                      if (!launched && context.mounted) {
                        NotificationService.error(
                            context, 'Impossible de lancer le téléchargement');
                      }
                    } catch (error) {
                      if (context.mounted)
                        NotificationService.error(
                            context, 'Le téléchargement n\'a pas pu démarrer. Réessaie dans un instant.');
                    }
                  },
            icon: const Icon(Icons.download),
            label: const Text('Télécharger une copie'),
          ),
          FilledButton.icon(
            onPressed: isPublishing
                ? null
                : () async {
                    try {
                      await ref
                          .read(projectWorkspaceProvider.notifier)
                          .publishSite();
                      if (context.mounted)
                        NotificationService.success(
                            context, 'Ton site est en ligne. Tu peux maintenant partager le lien.');
                    } catch (e) {
                      if (context.mounted)
                        NotificationService.error(context,
                            'La mise en ligne n\'a pas abouti. Vérifie que ton site est prêt, puis réessaie.');
                    }
                  },
            icon: isPublishing
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.cloud_upload),
            label: Text(isPublishing ? 'Mise en ligne…' : 'Mettre en ligne'),
          ),
        ],
      ),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Mise en ligne du site',
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 4),
                Text(
                  publish.url == null
                      ? 'Ton site doit d\'abord être créé avant de pouvoir être mis en ligne.'
                      : 'Ton site est en ligne et accessible via le lien ci-dessous.',
                  style: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
                ),
                const SizedBox(height: 16),
                const Divider(height: 1),
                const SizedBox(height: 16),
                _DeployStep(
                    title: 'Site créé',
                    ready: publish.status != 'draft',
                    active: publish.status == 'building'),
                _DeployStep(
                    title: 'Mise en ligne',
                    ready: publish.status == 'uploading' ||
                        publish.status == 'published',
                    active: publish.status == 'uploading'),
                _DeployStep(
                    title: 'Adresse web et connexion sécurisée',
                    ready: publish.status == 'published',
                    active: false),
                if (publish.url != null) ...[
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                        color: const Color(0xFF10B981).withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                            color: const Color(0xFF10B981).withValues(alpha: 0.3))),
                    child: Row(
                      children: [
                        const Icon(Icons.check_circle,
                            color: Color(0xFF10B981)),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Site en ligne',
                                  style: TextStyle(
                                      fontWeight: FontWeight.w700,
                                      color: Color(0xFF10B981))),
                              const SizedBox(height: 2),
                              Text(publish.url!,
                                  style: const TextStyle(
                                      color: Color(0xFF0369A1),
                                      decoration: TextDecoration.underline,
                                      fontSize: 13)),
                            ],
                          ),
                        ),
                        IconButton(
                          tooltip: 'Copier le lien',
                          icon: const Icon(Icons.copy_outlined, size: 18),
                          onPressed: () {
                            Clipboard.setData(
                                ClipboardData(text: publish.url!));
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                  content: Text('Lien copié !'),
                                  duration: Duration(seconds: 2)));
                          },
                        ),
                        IconButton(
                          tooltip: 'Ouvrir dans le navigateur',
                          icon: const Icon(Icons.open_in_new, size: 18),
                          onPressed: () => launchUrl(
                              Uri.parse(publish.url!),
                              mode: LaunchMode.externalApplication),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _DeployStep extends StatelessWidget {
  const _DeployStep(
      {required this.title, required this.ready, required this.active});

  final String title;
  final bool ready;
  final bool active;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: active
          ? const SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2))
          : Icon(ready ? Icons.check_circle_outline : Icons.pending_outlined,
              color: ready ? const Color(0xFF10B981) : AppColors.textSecondary),
      title: Text(title),
      subtitle: Text(active
          ? 'En cours'
          : ready
              ? 'Terminé'
              : 'En attente'),
    );
  }
}
