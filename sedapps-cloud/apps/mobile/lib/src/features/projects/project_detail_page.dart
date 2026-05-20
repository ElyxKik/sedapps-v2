import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../agents/agent_state.dart';
import '../chat/chat_page.dart';
import '../cms/cms_page.dart';
import '../editor/editor_page.dart';
import '../preview/preview_page.dart';
import 'project_workspace_state.dart';
import '../publish/publish_page.dart';

class ProjectDetailPage extends ConsumerStatefulWidget {
  const ProjectDetailPage({required this.projectId, super.key});

  final String projectId;

  @override
  ConsumerState<ProjectDetailPage> createState() => _ProjectDetailPageState();
}

class _ProjectDetailPageState extends ConsumerState<ProjectDetailPage> {
  bool _autoSwitched = false;
  bool _deleting = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      ref.read(currentProjectIdProvider.notifier).state = widget.projectId;
      _loadProject();
      final jobId = ref.read(currentJobIdProvider);
      if (jobId != null && jobId.isNotEmpty) {
        _openWorkspace(_WorkspacePanel.chat);
      }
    });
  }

  Future<void> _loadProject() async {
    try {
      final data = await ref.read(apiClientProvider).project(widget.projectId);
      if (!mounted) return;
      ref.read(projectWorkspaceProvider.notifier).syncFromProject(data);
      // Log brief pour debug
      final brief = data['brief'];
      if (brief != null) {
        debugPrint('✓ Brief chargé: $brief');
      }
    } catch (e) {
      debugPrint('Erreur chargement projet: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(currentJobProvider, (previous, next) {
      next.whenData((job) {
        if (!_autoSwitched && job != null && job.status == 'success') {
          _autoSwitched = true;
          _loadProject();
          if (mounted) _openWorkspace(_WorkspacePanel.preview);
        }
      });
    });

    return ListView(
      padding: const EdgeInsets.fromLTRB(28, 28, 28, 32),
      children: [
        _ProjectHero(
          onBack: () => context.go('/projects'),
          onDelete: _confirmDeleteProject,
          isDeleting: _deleting,
        ),
        LayoutBuilder(
          builder: (context, constraints) {
            final columns = constraints.maxWidth > 900 ? 3 : constraints.maxWidth > 600 ? 2 : 1;
            return GridView.count(
              crossAxisCount: columns,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 2.2,
              children: _WorkspacePanel.values.map((panel) {
                return _WorkspaceCard(panel: panel, onTap: () => _openWorkspace(panel));
              }).toList(),
            );
          },
        ),
      ],
    );
  }

  Future<void> _openWorkspace(_WorkspacePanel panel) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: false,
      backgroundColor: AppColors.background,
      barrierColor: Colors.black.withValues(alpha: 0.55),
      constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width),
      builder: (context) {
        return _WorkspaceModal(panel: panel);
      },
    );
  }

  Future<void> _confirmDeleteProject() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Supprimer le projet ?'),
          content: const Text('Cette action est définitive. Le projet, ses contenus et ses tâches associées seront supprimés.'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Annuler'),
            ),
            FilledButton.icon(
              style: FilledButton.styleFrom(backgroundColor: Colors.red),
              onPressed: () => Navigator.of(context).pop(true),
              icon: const Icon(Icons.delete_outline),
              label: const Text('Supprimer'),
            ),
          ],
        );
      },
    );

    if (confirmed != true || !mounted) return;

    setState(() => _deleting = true);
    try {
      await ref.read(apiClientProvider).deleteProject(widget.projectId);
      if (!mounted) return;
      ref.read(currentProjectIdProvider.notifier).state = null;
      ref.read(currentJobIdProvider.notifier).state = null;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Projet supprimé')),
      );
      context.go('/projects');
    } catch (e) {
      if (!mounted) return;
      setState(() => _deleting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur suppression : $e')),
      );
    }
  }
}

enum _WorkspacePanel {
  chat(
    title: 'Générateur IA',
    subtitle: 'Chat multi-agents avec contexte du projet en mémoire.',
    icon: Icons.chat_bubble_outline,
    color: AppColors.skyBlue,
  ),
  preview(
    title: 'Aperçu',
    subtitle: 'Visualise le site généré en plein écran.',
    icon: Icons.visibility_outlined,
    color: Color(0xFF6366F1),
  ),
  editor(
    title: 'Éditeur',
    subtitle: 'Modifie les sections, textes et design tokens.',
    icon: Icons.web_outlined,
    color: Color(0xFF14B8A6),
  ),
  cms(
    title: 'Articles / CMS',
    subtitle: 'Crée, publie et organise les contenus du site.',
    icon: Icons.article_outlined,
    color: Color(0xFFF59E0B),
  ),
  publish(
    title: 'Publication',
    subtitle: 'Prépare le domaine et lance le déploiement.',
    icon: Icons.cloud_upload_outlined,
    color: Color(0xFF10B981),
  );

  const _WorkspacePanel({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
}

class _ProjectHero extends StatelessWidget {
  const _ProjectHero({required this.onBack, required this.onDelete, required this.isDeleting});

  final VoidCallback onBack;
  final VoidCallback onDelete;
  final bool isDeleting;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              AppColors.skyBlue.withValues(alpha: 0.12),
              AppColors.skyBlueAccent.withValues(alpha: 0.08),
              Colors.white,
            ],
          ),
        ),
        child: LayoutBuilder(
          builder: (context, constraints) {
            final compact = constraints.maxWidth < 620;
            final title = Row(
              children: [
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    color: AppColors.skyBlue,
                    borderRadius: BorderRadius.circular(18),
                    boxShadow: [BoxShadow(color: AppColors.skyBlue.withValues(alpha: 0.25), blurRadius: 24, offset: const Offset(0, 10))],
                  ),
                  child: const Icon(Icons.dashboard_customize_outlined, color: Colors.white, size: 28),
                ),
                const SizedBox(width: 18),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Espace projet', style: Theme.of(context).textTheme.headlineMedium),
                      const SizedBox(height: 6),
                      Text(
                        'Ouvre chaque espace en plein écran : chat, aperçu, articles, éditeur ou publication.',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
              ],
            );
            final actions = Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: compact ? WrapAlignment.start : WrapAlignment.end,
              children: [
                OutlinedButton.icon(
                  onPressed: onBack,
                  icon: const Icon(Icons.arrow_back, size: 18),
                  label: const Text('Retour'),
                ),
                OutlinedButton.icon(
                  onPressed: isDeleting ? null : onDelete,
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.red,
                    side: const BorderSide(color: Colors.red),
                  ),
                  icon: isDeleting
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.delete_outline, size: 18),
                  label: Text(isDeleting ? 'Suppression…' : 'Supprimer'),
                ),
              ],
            );
            if (compact) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  title,
                  const SizedBox(height: 16),
                  actions,
                ],
              );
            }
            return Row(
              children: [
                Expanded(child: title),
                const SizedBox(width: 12),
                actions,
              ],
            );
          },
        ),
      ),
    );
  }
}

class _WorkspaceCard extends StatelessWidget {
  const _WorkspaceCard({required this.panel, required this.onTap});

  final _WorkspacePanel panel;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: panel.color.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(panel.icon, color: panel.color, size: 18),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      panel.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      panel.subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Icon(Icons.chevron_right, color: panel.color, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

class _WorkspaceModal extends StatelessWidget {
  const _WorkspaceModal({required this.panel});

  final _WorkspacePanel panel;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SizedBox(
        height: MediaQuery.sizeOf(context).height,
        width: MediaQuery.sizeOf(context).width,
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.fromLTRB(20, 14, 12, 14),
              decoration: const BoxDecoration(
                color: AppColors.surface,
                border: Border(bottom: BorderSide(color: AppColors.border)),
              ),
              child: Row(
                children: [
                  Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(
                      color: panel.color.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Icon(panel.icon, color: panel.color),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(panel.title, style: Theme.of(context).textTheme.titleLarge),
                        const SizedBox(height: 2),
                        Text(panel.subtitle, maxLines: 1, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall),
                      ],
                    ),
                  ),
                  IconButton(
                    tooltip: 'Fermer',
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
            ),
            Expanded(child: _panelContent(panel)),
          ],
        ),
      ),
    );
  }

  Widget _panelContent(_WorkspacePanel panel) {
    return switch (panel) {
      _WorkspacePanel.chat => const ChatPage(),
      _WorkspacePanel.preview => const PreviewPage(),
      _WorkspacePanel.editor => const EditorPage(),
      _WorkspacePanel.cms => const CmsPage(),
      _WorkspacePanel.publish => const PublishPage(),
    };
  }
}
