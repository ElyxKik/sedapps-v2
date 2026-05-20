import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

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
    final isPublishing = publish.status == 'building' || publish.status == 'uploading';
    final projectId = ref.watch(currentProjectIdProvider);
    return PageScaffold(
      title: 'Publication',
      action: Wrap(
        spacing: 10,
        children: [
          OutlinedButton.icon(
            onPressed: projectId == null
                ? null
                : () async {
                    try {
                      final url = await ref.read(apiClientProvider).projectDownloadUrl(projectId);
                      final launched = await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
                      if (!launched && context.mounted) {
                        NotificationService.error(context, 'Impossible de lancer le téléchargement');
                      }
                    } catch (error) {
                      if (context.mounted) NotificationService.error(context, 'Téléchargement indisponible : $error');
                    }
                  },
            icon: const Icon(Icons.download),
            label: const Text('Télécharger'),
          ),
          FilledButton.icon(
            onPressed: isPublishing
                ? null
                : () async {
                    await ref.read(projectWorkspaceProvider.notifier).publishSite();
                    if (context.mounted) NotificationService.success(context, 'Site publié avec succès');
                  },
            icon: isPublishing ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.cloud_upload),
            label: Text(isPublishing ? 'Déploiement...' : 'Déployer'),
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
                Text('Canaux de publication', style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 12),
                SwitchListTile(
                  value: publish.subdomainEnabled,
                  onChanged: (value) => ref.read(projectWorkspaceProvider.notifier).updatePublish(subdomainEnabled: value),
                  title: const Text('Sous-domaine SedApps'),
                  subtitle: Text(publish.domain),
                ),
                SwitchListTile(
                  value: publish.customDomainEnabled,
                  onChanged: (value) => ref.read(projectWorkspaceProvider.notifier).updatePublish(customDomainEnabled: value),
                  title: const Text('Domaine personnalisé'),
                  subtitle: const Text('Configuration DNS OVH automatisée'),
                ),
                TextField(
                  controller: TextEditingController(text: publish.domain),
                  decoration: const InputDecoration(labelText: 'Domaine de publication', prefixIcon: Icon(Icons.language)),
                  onSubmitted: (value) => ref.read(projectWorkspaceProvider.notifier).updatePublish(domain: value),
                ),
                const Divider(),
                _DeployStep(title: 'Build statique Next.js', ready: publish.status != 'draft', active: publish.status == 'building'),
                _DeployStep(title: 'Upload OVH Object Storage', ready: publish.status == 'uploading' || publish.status == 'published', active: publish.status == 'uploading'),
                _DeployStep(title: 'DNS + SSL', ready: publish.status == 'published', active: false),
                if (publish.url != null) ...[
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(color: const Color(0xFF10B981).withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12)),
                    child: Row(
                      children: [
                        const Icon(Icons.check_circle, color: Color(0xFF10B981)),
                        const SizedBox(width: 12),
                        Expanded(child: Text('Site disponible : ${publish.url}', style: const TextStyle(fontWeight: FontWeight.w700))),
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
  const _DeployStep({required this.title, required this.ready, required this.active});

  final String title;
  final bool ready;
  final bool active;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: active
          ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2))
          : Icon(ready ? Icons.check_circle_outline : Icons.pending_outlined, color: ready ? const Color(0xFF10B981) : AppColors.textSecondary),
      title: Text(title),
      subtitle: Text(active ? 'En cours' : ready ? 'Terminé' : 'En attente'),
    );
  }
}
