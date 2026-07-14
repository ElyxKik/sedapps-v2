import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import '../../widgets/animations.dart';
import '../../widgets/dialogs.dart';
import '../../widgets/notifications.dart';
import '../../widgets/page_scaffold.dart';
import '../agents/agent_models.dart';
import '../agents/agent_state.dart';
import 'data/project_repository.dart';
import 'domain/project.dart';

class ProjectsPage extends ConsumerStatefulWidget {
  const ProjectsPage({super.key});

  @override
  ConsumerState<ProjectsPage> createState() => _ProjectsPageState();
}

class _ProjectsPageState extends ConsumerState<ProjectsPage> {
  late Future<List<Project>> _projectsFuture;

  @override
  void initState() {
    super.initState();
    _projectsFuture =
        ref.read(projectRepositoryProvider).list().then((projects) {
      _checkAndRestoreActiveJob(projects);
      return projects;
    });
  }

  void _reloadProjects() {
    setState(() {
      _projectsFuture =
          ref.read(projectRepositoryProvider).list().then((projects) {
        _checkAndRestoreActiveJob(projects);
        return projects;
      });
    });
  }

  void _checkAndRestoreActiveJob(List<Project> projects) {
    for (final project in projects) {
      if (project.isGenerating && project.activeJobId != null) {
        final jobId = project.activeJobId!;
        final projectId = project.id;
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!mounted) return;
          final currentJobId = ref.read(currentJobIdProvider);
          if (currentJobId != jobId) {
            ref.read(currentJobIdProvider.notifier).state = jobId;
          }
          final currentJobProjectId = ref.read(currentJobProjectIdProvider);
          if (currentJobProjectId != projectId) {
            ref.read(currentJobProjectIdProvider.notifier).state = projectId;
          }
        });
        break;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentJobId = ref.watch(currentJobIdProvider);

    return PageScaffold(
      title: 'Mes sites',
      subtitle: 'Gère et publie tes sites créés avec Sala AI',
      action: FilledButton.icon(
        onPressed: () => context.go('/new-site'),
        icon: const Icon(Icons.add, size: 18),
        label: const Text('Nouveau site'),
      ),
      children: [
        FutureBuilder<List<Project>>(
          future: _projectsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(
                  child: Padding(
                      padding: EdgeInsets.all(40),
                      child: CircularProgressIndicator()));
            }
            final projects = snapshot.data ?? [];

            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (projects.isEmpty)
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                          vertical: 60, horizontal: 40),
                      child: Column(
                        children: [
                          Container(
                            width: 80,
                            height: 80,
                            decoration: BoxDecoration(
                                color: AppColors.skyBlueLight,
                                borderRadius: BorderRadius.circular(24)),
                            child: const Icon(Icons.folder_open,
                                size: 40, color: AppColors.skyBlue),
                          ),
                          const SizedBox(height: 20),
                          Text('Aucun site pour le moment',
                              style: Theme.of(context).textTheme.headlineSmall),
                          const SizedBox(height: 8),
                          const Text(
                              'Crée ton premier site en quelques minutes. Tu pourras choisir le style, les couleurs, les pages et l\'adresse de ton site.',
                              style: TextStyle(color: AppColors.textSecondary)),
                          const SizedBox(height: 24),
                          FilledButton.icon(
                            onPressed: () => context.go('/new-site'),
                            icon: const Icon(Icons.rocket_launch, size: 18),
                            label: const Text('Créer mon premier site'),
                          ),
                        ],
                      ),
                    ),
                  )
                else
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final width = constraints.maxWidth;
                      final columns = width > 1300
                          ? 4
                          : width > 900
                              ? 3
                              : width > 550
                                  ? 2
                                  : 1;
                      final spacing = width < 420 ? 10.0 : 16.0;
                      final aspectRatio = width < 420
                          ? 1.95
                          : width < 600
                              ? 1.7
                              : width < 950
                                  ? 1.45
                                  : 1.55;
                      return GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: projects.length,
                        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: columns,
                          crossAxisSpacing: spacing,
                          mainAxisSpacing: spacing,
                          childAspectRatio: aspectRatio,
                        ),
                        itemBuilder: (context, index) {
                          final project = projects[index];
                          return FadeInUp(
                            delay: Duration(milliseconds: index * 100),
                            child: _ProjectCard(
                              project: project,
                              repository: ref.read(projectRepositoryProvider),
                              onDeleted: _reloadProjects,
                            ),
                          );
                        },
                      );
                    },
                  ),
              ],
            );
          },
        ),
      ],
    );
  }
}

class _ProjectCard extends StatefulWidget {
  const _ProjectCard(
      {required this.project,
      required this.repository,
      required this.onDeleted});

  final Project project;
  final ProjectRepository repository;
  final VoidCallback onDeleted;

  @override
  State<_ProjectCard> createState() => _ProjectCardState();
}

class _ProjectCardState extends State<_ProjectCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final isPublished = widget.project.isPublished;
    final color =
        isPublished ? const Color(0xFF10B981) : const Color(0xFFF59E0B);
    final compact = MediaQuery.sizeOf(context).width < 420;

    return Card(
      child: InkWell(
        onTap: () => context.go('/projects/${widget.project.id}'),
        onHover: (value) => setState(() => _isHovered = value),
        child: Padding(
          padding: EdgeInsets.all(compact ? 14 : 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: compact ? 40 : 48,
                    height: compact ? 40 : 48,
                    decoration: BoxDecoration(
                      gradient: isPublished
                          ? const LinearGradient(
                              colors: [Color(0xFF10B981), Color(0xFF34D399)])
                          : const LinearGradient(
                              colors: [Color(0xFFF59E0B), Color(0xFFFBBF24)]),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Icon(isPublished ? Icons.public : Icons.edit_note,
                        color: Colors.white, size: compact ? 20 : 24),
                  ),
                  const Spacer(),
                  SizedBox(
                    width: 40,
                    child: PopupMenuButton(
                      itemBuilder: (_) => [
                        PopupMenuItem(
                          child: const Text('Éditer'),
                          onTap: () =>
                              context.go('/projects/${widget.project.id}'),
                        ),
                        PopupMenuItem(
                          child: const Text('Supprimer le site'),
                          onTap: () => showConfirmDialog(
                            context,
                            title: 'Supprimer le site',
                            message:
                                'Es-tu sûr de vouloir supprimer ce site ? Cette action est irréversible.',
                            confirmText: 'Supprimer',
                            isDangerous: true,
                            onConfirm: () async {
                              await widget.repository.delete(widget.project.id);
                              widget.onDeleted();
                              if (context.mounted)
                                NotificationService.error(
                                    context, 'Site supprimé');
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const Spacer(),
              Text(widget.project.name,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontSize: compact ? 15 : null),
                  maxLines: compact ? 1 : 2,
                  overflow: TextOverflow.ellipsis),
              if (widget.project.defaultDomain != null) ...[
                const SizedBox(height: 3),
                Text(widget.project.defaultDomain!,
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: AppColors.skyBlue),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis),
              ],
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.calendar_today_outlined,
                      size: 12, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Expanded(
                      child: Text(_formatDate(widget.project.createdAt),
                          style: Theme.of(context).textTheme.bodySmall,
                          overflow: TextOverflow.ellipsis)),
                  if (isPublished) ...[
                    Icon(Icons.public_outlined,
                        size: 12, color: const Color(0xFF10B981)),
                    const SizedBox(width: 4),
                    Text('En ligne',
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: const Color(0xFF10B981))),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(DateTime? value) {
    if (value == null) return 'Date inconnue';
    final date = value;
    return 'Créé le ${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
  }
}
