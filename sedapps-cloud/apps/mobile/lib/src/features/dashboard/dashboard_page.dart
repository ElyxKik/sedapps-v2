import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../../widgets/animations.dart';
import '../../widgets/page_scaffold.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projectsFuture = ref.watch(apiClientProvider).projects();
    return PageScaffold(
      title: 'Bonjour 👋',
      subtitle: 'Voici un aperçu de ton activité aujourd\'hui.',
      action: FilledButton.icon(
        onPressed: () => context.go('/new-site'),
        icon: const Icon(Icons.add, size: 18),
        label: const Text('Nouveau site'),
      ),
      children: [
        FadeInUp(
          child: HeroBanner(
            title: 'Crée ton prochain site avec l\'IA',
            subtitle: 'Décris ton projet, nos agents IA livrent un site complet en quelques minutes.',
            actionLabel: 'Démarrer maintenant',
            onAction: () => context.go('/new-site'),
          ),
        ),
        const SizedBox(height: 28),
        FutureBuilder<List<dynamic>>(
          future: projectsFuture,
          builder: (context, snapshot) {
            final projects = snapshot.data ?? [];
            final publishedCount = projects.where((project) {
              final item = Map<String, dynamic>.from(project as Map);
              return item['status']?.toString() == 'published';
            }).length;
            final draftCount = projects.length - publishedCount;
            return LayoutBuilder(
              builder: (context, constraints) {
                final width = constraints.maxWidth;
                final columns = width > 1100 ? 4 : width > 720 ? 3 : 2;
                final spacing = width < 380 ? 10.0 : 16.0;
                final tileWidth = (width - spacing * (columns - 1)) / columns;
                final aspectRatio = (tileWidth / (tileWidth < 160 ? 128 : tileWidth < 220 ? 138 : 150)).clamp(1.05, 1.8);
                return GridView.count(
                  crossAxisCount: columns,
                  crossAxisSpacing: spacing,
                  mainAxisSpacing: spacing,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  childAspectRatio: aspectRatio,
                  children: [
                    FadeInUp(delay: const Duration(milliseconds: 100), child: StatCard(label: 'Projets', value: snapshot.connectionState == ConnectionState.waiting ? '...' : projects.length.toString(), icon: Icons.folder_copy_outlined, color: AppColors.skyBlue)),
                    FadeInUp(delay: const Duration(milliseconds: 200), child: StatCard(label: 'Sites publiés', value: snapshot.connectionState == ConnectionState.waiting ? '...' : publishedCount.toString(), icon: Icons.public, color: const Color(0xFF10B981))),
                    FadeInUp(delay: const Duration(milliseconds: 300), child: StatCard(label: 'Brouillons', value: snapshot.connectionState == ConnectionState.waiting ? '...' : draftCount.toString(), icon: Icons.edit_note, color: const Color(0xFF6366F1))),
                    FadeInUp(delay: const Duration(milliseconds: 400), child: const StatCard(label: 'Backend', value: 'Live', icon: Icons.cloud_done_outlined, trend: 'API', color: Color(0xFFF59E0B))),
                  ],
                );
              },
            );
          },
        ),
        const SizedBox(height: 28),
        LayoutBuilder(
          builder: (context, constraints) {
            final wide = constraints.maxWidth > 900;
            final left = _RecentProjects(projectsFuture: projectsFuture);
            final right = const _QuickActions();
            if (!wide) {
              return Column(children: [left, const SizedBox(height: 20), right]);
            }
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(flex: 2, child: left),
                const SizedBox(width: 20),
                Expanded(flex: 1, child: right),
              ],
            );
          },
        ),
      ],
    );
  }
}

class _RecentProjects extends StatelessWidget {
  const _RecentProjects({required this.projectsFuture});
  final Future<List<dynamic>> projectsFuture;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SectionHeader(
              title: 'Projets récents',
              subtitle: 'Tes derniers sites créés avec l\'IA',
              trailing: TextButton(
                onPressed: () => context.go('/projects'),
                child: const Text('Voir tout'),
              ),
            ),
            FutureBuilder<List<dynamic>>(
              future: projectsFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Padding(padding: EdgeInsets.all(40), child: Center(child: CircularProgressIndicator()));
                }
                final projects = snapshot.data ?? [];
                if (projects.isEmpty) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 32),
                    child: Center(
                      child: Column(
                        children: [
                          Container(
                            width: 64, height: 64,
                            decoration: BoxDecoration(color: AppColors.skyBlueLight, borderRadius: BorderRadius.circular(20)),
                            child: const Icon(Icons.folder_open, size: 32, color: AppColors.skyBlue),
                          ),
                          const SizedBox(height: 16),
                          Text('Aucun projet', style: Theme.of(context).textTheme.titleMedium),
                          const SizedBox(height: 4),
                          const Text('Crée ton premier site avec l\'IA.', style: TextStyle(color: AppColors.textSecondary)),
                        ],
                      ),
                    ),
                  );
                }
                return Column(
                  children: [
                    for (final project in projects.take(5))
                      _ProjectRow(project: Map<String, dynamic>.from(project as Map)),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _ProjectRow extends StatelessWidget {
  const _ProjectRow({required this.project});
  final Map<String, dynamic> project;

  @override
  Widget build(BuildContext context) {
    final status = project['status']?.toString() ?? 'draft';
    final published = status == 'published';
    return InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () => context.go('/projects/${project['id']}'),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
        child: Row(
          children: [
            Container(
              width: 44, height: 44,
              decoration: BoxDecoration(
                gradient: published
                    ? const LinearGradient(colors: [Color(0xFF10B981), Color(0xFF34D399)])
                    : const LinearGradient(colors: [AppColors.skyBlue, AppColors.skyBlueAccent]),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(published ? Icons.public : Icons.edit_note, color: Colors.white, size: 22),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(project['name']?.toString() ?? 'Projet',
                      style: Theme.of(context).textTheme.titleSmall, maxLines: 1, overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 2),
                  Text(published ? 'Site publié · en ligne' : 'Brouillon · à finaliser',
                      style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppColors.textSecondary),
          ],
        ),
      ),
    );
  }
}

class _QuickActions extends StatelessWidget {
  const _QuickActions();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SectionHeader(title: 'Actions rapides'),
            _ActionTile(icon: Icons.add_circle_outline, color: AppColors.skyBlue, title: 'Nouveau site', desc: 'Lance la création IA', onTap: () => context.go('/new-site')),
            _ActionTile(icon: Icons.article_outlined, color: const Color(0xFFF59E0B), title: 'Nouvel article', desc: 'Rédige du contenu SEO', onTap: () => context.go('/cms')),
            _ActionTile(icon: Icons.cloud_upload_outlined, color: const Color(0xFF10B981), title: 'Publier un site', desc: 'Déploie sur OVH', onTap: () {}),
            _ActionTile(icon: Icons.analytics_outlined, color: const Color(0xFF6366F1), title: 'Voir analytics', desc: 'Stats visiteurs', onTap: () {}),
          ],
        ),
      ),
    );
  }
}

class _ActionTile extends StatelessWidget {
  const _ActionTile({required this.icon, required this.color, required this.title, required this.desc, required this.onTap});
  final IconData icon;
  final Color color;
  final String title;
  final String desc;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 4),
        child: Row(
          children: [
            Container(
              width: 40, height: 40,
              decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
                  Text(desc, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios, size: 14, color: AppColors.textSecondary),
          ],
        ),
      ),
    );
  }
}
