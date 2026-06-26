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
  bool _renaming = false;
  bool _regenerating = false;
  String? _projectName;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      ref.read(currentProjectIdProvider.notifier).state = widget.projectId;
      _loadProject();
    });
  }

  Future<void> _loadProject() async {
    try {
      final data = await ref.read(apiClientProvider).project(widget.projectId);
      if (!mounted) return;
      setState(() {
        _projectName = data['name']?.toString();
      });
      ref.read(projectWorkspaceProvider.notifier).syncFromProject(data);
      // Log brief pour debug
      final brief = data['brief'];
      if (brief != null) {
        debugPrint('✓ Brief chargé: $brief');
      }
      // Si le projet est en cours de génération, restaurer le job actif
      if (data['status'] == 'generating' && data['active_job_id'] != null) {
        final jobId = data['active_job_id'].toString();
        final currentJobId = ref.read(currentJobIdProvider);
        if (currentJobId != jobId) {
          ref.read(currentJobIdProvider.notifier).state = jobId;
          _openWorkspace(_WorkspacePanel.chat);
        }
      } else {
        ref.read(currentJobIdProvider.notifier).state = null;
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
          projectName: _projectName,
          onBack: () => context.go('/projects'),
          onDelete: _confirmDeleteProject,
          onRename: _confirmRenameProject,
          onRegenerate: _confirmRegenerateProject,
          isDeleting: _deleting,
          isRenaming: _renaming,
          isRegenerating: _regenerating,
        ),
        const SizedBox(height: 24),
        LayoutBuilder(
          builder: (context, constraints) {
            final width = constraints.maxWidth;
            final columns = width > 1200
                ? 4
                : width > 850
                    ? 3
                    : width > 550
                        ? 2
                        : 1;
            final aspectRatio = width > 1200
                ? 2.6
                : width > 850
                    ? 2.3
                    : width > 550
                        ? 2.2
                        : 2.5;
            return GridView.count(
              crossAxisCount: columns,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: aspectRatio,
              children: _WorkspacePanel.values.map((panel) {
                return _WorkspaceCard(
                    panel: panel, onTap: () => _openWorkspace(panel));
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

  Future<void> _confirmRenameProject() async {
    final ctrl = TextEditingController(text: _projectName ?? '');
    final newName = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Renommer le site'),
        content: TextField(
          controller: ctrl,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Nouveau nom',
            hintText: 'Ex\u00a0: Boulangerie Martin',
          ),
          onSubmitted: (v) => Navigator.of(context).pop(v.trim()),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(null),
            child: const Text('Annuler'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(ctrl.text.trim()),
            child: const Text('Enregistrer'),
          ),
        ],
      ),
    );
    ctrl.dispose();
    if (newName == null || newName.isEmpty || !mounted) return;
    setState(() => _renaming = true);
    try {
      await ref.read(apiClientProvider).updateProject(
          widget.projectId, {'name': newName});
      if (!mounted) return;
      setState(() => _projectName = newName);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Site renomm\u00e9 avec succ\u00e8s')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Impossible de renommer le site. R\u00e9essaie.')),
      );
    } finally {
      if (mounted) setState(() => _renaming = false);
    }
  }

  Future<void> _confirmRegenerateProject() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('R\u00e9g\u00e9n\u00e9rer le site ?'),
        content: const Text(
            'Le site existant sera remplac\u00e9 par une nouvelle version g\u00e9n\u00e9r\u00e9e par l\u2019IA. Cette action peut prendre quelques minutes.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Annuler'),
          ),
          FilledButton.icon(
            onPressed: () => Navigator.of(context).pop(true),
            icon: const Icon(Icons.refresh),
            label: const Text('R\u00e9g\u00e9n\u00e9rer'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _regenerating = true);
    try {
      final job = await ref
          .read(apiClientProvider)
          .generateSite(widget.projectId);
      final jobId = job['job_id']?.toString() ?? job['id']?.toString();
      ref.read(currentJobIdProvider.notifier).state = jobId;
      ref.read(currentJobProjectIdProvider.notifier).state = widget.projectId;
      _autoSwitched = false;
      if (!mounted) return;
      _openWorkspace(_WorkspacePanel.chat);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Impossible de lancer la r\u00e9g\u00e9n\u00e9ration. R\u00e9essaie.')),
      );
    } finally {
      if (mounted) setState(() => _regenerating = false);
    }
  }

  Future<void> _confirmDeleteProject() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Supprimer le site ?'),
          content: const Text(
              'Cette action est définitive. Le site, ses contenus et ses informations associées seront supprimés.'),
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
        const SnackBar(content: Text('Site supprimé')),
      );
      context.go('/projects');
    } catch (e) {
      if (!mounted) return;
      setState(() => _deleting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('La suppression n\'a pas abouti. Réessaie.')),
      );
    }
  }
}

enum _WorkspacePanel {
  chat(
    title: 'Modifier le site',
    subtitle: 'Demande des modifications à Sala AI en langage simple.',
    icon: Icons.auto_fix_high,
    color: AppColors.skyBlue,
  ),
  preview(
    title: 'Aperçu',
    subtitle: 'Visualise ton site en plein écran.',
    icon: Icons.visibility_outlined,
    color: Color(0xFF0EA5E9),
  ),
  editor(
    title: 'Éditeur',
    subtitle: 'Modifie les textes, les couleurs et le style de ton site.',
    icon: Icons.web_outlined,
    color: Color(0xFF14B8A6),
  ),
  cms(
    title: 'Contenus',
    subtitle: 'Crée, publie et organise les contenus du site.',
    icon: Icons.article_outlined,
    color: Color(0xFFF59E0B),
  ),
  publish(
    title: 'Mettre en ligne',
    subtitle: 'Prépare l\'adresse de ton site et mets-le en ligne.',
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
  const _ProjectHero({
    required this.onBack,
    required this.onDelete,
    required this.onRename,
    required this.onRegenerate,
    required this.isDeleting,
    required this.isRenaming,
    required this.isRegenerating,
    this.projectName,
  });

  final VoidCallback onBack;
  final VoidCallback onDelete;
  final VoidCallback onRename;
  final VoidCallback onRegenerate;
  final bool isDeleting;
  final bool isRenaming;
  final bool isRegenerating;
  final String? projectName;

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
                    boxShadow: [
                      BoxShadow(
                          color: AppColors.skyBlue.withValues(alpha: 0.25),
                          blurRadius: 24,
                          offset: const Offset(0, 10))
                    ],
                  ),
                  child: const Icon(Icons.dashboard_customize_outlined,
                      color: Colors.white, size: 28),
                ),
                const SizedBox(width: 18),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        projectName != null ? 'Espace site - $projectName' : 'Espace site',
                        style: Theme.of(context).textTheme.headlineMedium,
                      ),
                      const SizedBox(height: 6),
                      Text(
                        'Ouvre chaque espace en plein écran : chat, aperçu, articles, éditeur ou publication.',
                        style: Theme.of(context)
                            .textTheme
                            .bodyMedium
                            ?.copyWith(color: AppColors.textSecondary),
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
                  onPressed: isRenaming ? null : onRename,
                  icon: isRenaming
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.edit_outlined, size: 18),
                  label: Text(isRenaming ? 'Sauvegarde…' : 'Renommer'),
                ),
                OutlinedButton.icon(
                  onPressed: isRegenerating ? null : onRegenerate,
                  icon: isRegenerating
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.refresh, size: 18),
                  label: Text(isRegenerating ? 'Lancement…' : 'Régénérer'),
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
                      style: Theme.of(context)
                          .textTheme
                          .titleSmall
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      panel.subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                          fontSize: 11, color: AppColors.textSecondary),
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
                        Text(panel.title,
                            style: Theme.of(context).textTheme.titleLarge),
                        const SizedBox(height: 2),
                        Text(panel.subtitle,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.bodySmall),
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
