import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../../widgets/animations.dart';
import '../../widgets/dialogs.dart';
import '../../widgets/notifications.dart';
import '../../widgets/page_scaffold.dart';

class ProjectsPage extends ConsumerStatefulWidget {
  const ProjectsPage({super.key});

  @override
  ConsumerState<ProjectsPage> createState() => _ProjectsPageState();
}

class _ProjectsPageState extends ConsumerState<ProjectsPage> {
  late Future<List<dynamic>> _projectsFuture;

  @override
  void initState() {
    super.initState();
    _projectsFuture = ref.read(apiClientProvider).projects();
  }

  void _reloadProjects() {
    setState(() {
      _projectsFuture = ref.read(apiClientProvider).projects();
    });
  }

  @override
  Widget build(BuildContext context) {
    return PageScaffold(
      title: 'Mes projets',
      subtitle: 'Gère et publie tes sites créés avec l\'IA',
      action: FilledButton.icon(
        onPressed: () => context.go('/new-site'),
        icon: const Icon(Icons.add, size: 18),
        label: const Text('Nouveau site'),
      ),
      children: [
        FutureBuilder<List<dynamic>>(
          future: _projectsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: Padding(padding: EdgeInsets.all(40), child: CircularProgressIndicator()));
            }
            final projects = snapshot.data ?? [];
            if (projects.isEmpty) {
              return Card(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 60, horizontal: 40),
                  child: Column(
                    children: [
                      Container(
                        width: 80, height: 80,
                        decoration: BoxDecoration(color: AppColors.skyBlueLight, borderRadius: BorderRadius.circular(24)),
                        child: const Icon(Icons.folder_open, size: 40, color: AppColors.skyBlue),
                      ),
                      const SizedBox(height: 20),
                      Text('Aucun projet pour le moment', style: Theme.of(context).textTheme.headlineSmall),
                      const SizedBox(height: 8),
                      const Text('Crée ton premier site avec l\'IA en quelques minutes.',
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
              );
            }
            return LayoutBuilder(
              builder: (context, constraints) {
                final width = constraints.maxWidth;
                final columns = width > 1000 ? 3 : width > 600 ? 2 : 1;
                final spacing = width < 420 ? 10.0 : 16.0;
                final aspectRatio = width < 420 ? 1.95 : width < 600 ? 1.7 : 1.3;
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
                    final project = projects[index] as Map;
                    return FadeInUp(
                      delay: Duration(milliseconds: index * 100),
                      child: _ProjectCard(
                        project: Map<String, dynamic>.from(project),
                        api: ref.read(apiClientProvider),
                        onDeleted: _reloadProjects,
                      ),
                    );
                  },
                );
              },
            );
          },
        ),
      ],
    );
  }
}

class _ProjectCard extends StatefulWidget {
  const _ProjectCard({required this.project, required this.api, required this.onDeleted});

  final Map<String, dynamic> project;
  final ApiClient api;
  final VoidCallback onDeleted;

  @override
  State<_ProjectCard> createState() => _ProjectCardState();
}

class _ProjectCardState extends State<_ProjectCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final status = widget.project['status']?.toString() ?? 'draft';
    final isPublished = status == 'published';
    final color = isPublished ? const Color(0xFF10B981) : const Color(0xFFF59E0B);
    final compact = MediaQuery.sizeOf(context).width < 420;

    return Card(
      child: InkWell(
        onTap: () => context.go('/projects/${widget.project['id']}'),
        onHover: (value) => setState(() => _isHovered = value),
        child: Padding(
          padding: EdgeInsets.all(compact ? 14 : 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: compact ? 40 : 48, height: compact ? 40 : 48,
                    decoration: BoxDecoration(
                      gradient: isPublished
                          ? const LinearGradient(colors: [Color(0xFF10B981), Color(0xFF34D399)])
                          : const LinearGradient(colors: [Color(0xFFF59E0B), Color(0xFFFBBF24)]),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Icon(isPublished ? Icons.public : Icons.edit_note, color: Colors.white, size: compact ? 20 : 24),
                  ),
                  const Spacer(),
                  SizedBox(
                    width: 40,
                    child: PopupMenuButton(
                      itemBuilder: (_) => [
                        PopupMenuItem(
                          child: const Text('Éditer'),
                          onTap: () => context.go('/projects/${widget.project['id']}'),
                        ),
                        PopupMenuItem(
                          child: const Text('Supprimer'),
                          onTap: () => showConfirmDialog(
                            context,
                            title: 'Supprimer le projet',
                            message: 'Es-tu sûr de vouloir supprimer ce projet ? Cette action est irréversible.',
                            confirmText: 'Supprimer',
                            isDangerous: true,
                            onConfirm: () async {
                              await widget.api.deleteProject(widget.project['id'].toString());
                              widget.onDeleted();
                              if (context.mounted) NotificationService.error(context, 'Projet supprimé');
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const Spacer(),
              Text(widget.project['name']?.toString() ?? 'Projet sans nom',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: compact ? 15 : null),
                  maxLines: compact ? 1 : 2,
                  overflow: TextOverflow.ellipsis),
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.calendar_today_outlined, size: 12, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Expanded(child: Text(_formatDate(widget.project['created_at']), style: Theme.of(context).textTheme.bodySmall, overflow: TextOverflow.ellipsis)),
                  if (isPublished) ...[
                    Icon(Icons.visibility_outlined, size: 12, color: AppColors.textSecondary),
                    const SizedBox(width: 4),
                    Text('1.2k vues', style: Theme.of(context).textTheme.bodySmall),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(dynamic value) {
    if (value == null) return 'Date inconnue';
    final date = DateTime.tryParse(value.toString());
    if (date == null) return 'Date inconnue';
    return 'Créé le ${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
  }
}
