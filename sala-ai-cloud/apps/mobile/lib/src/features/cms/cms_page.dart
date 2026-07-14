import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../widgets/dialogs.dart';
import '../../widgets/notifications.dart';
import '../projects/project_workspace_state.dart' show currentProjectIdProvider;
import 'data/cms_repository.dart';
import 'domain/cms_models.dart';
import 'tabs/content_tabs.dart';
import 'controllers/article_controller.dart';

// ─────────────────────────────────────────────────────────────────────────────
// CmsPage — intégrée dans le workspace projet
// Clone complet du CmsHubPage avec onglet Blog connecté à l'API du projet
// ─────────────────────────────────────────────────────────────────────────────

class CmsPage extends ConsumerStatefulWidget {
  const CmsPage({super.key});

  @override
  ConsumerState<CmsPage> createState() => _CmsPageState();
}

class _CmsPageState extends ConsumerState<CmsPage> {
  int _selected = 0;

  static const _sections = [
    _CmsSection('Articles', Icons.article_outlined, Icons.article_rounded,
        'Articles & catégories', AppColors.skyBlue),
    _CmsSection(
        'Messages reçus',
        Icons.dynamic_form_outlined,
        Icons.dynamic_form_rounded,
        'Contact, devis, newsletter',
        Color(0xFF10B981)),
    _CmsSection('Avis et commentaires', Icons.comment_outlined,
        Icons.comment_rounded, 'Modération', Color(0xFFF59E0B)),
    _CmsSection('Pages du site', Icons.web_outlined, Icons.web_rounded,
        'À propos, Contact, Légal', Color(0xFF0EA5E9)),
    _CmsSection('Images et fichiers', Icons.image_outlined, Icons.image_rounded,
        'Images, vidéos, documents', Color(0xFF22D3EE)),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.background,
      child: Column(
        children: [
          // ── Stats strip ────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
            child: _StatsRow(projectId: ref.watch(currentProjectIdProvider)),
          ),
          const SizedBox(height: 16),
          // ── Navigation ────────────────────────────────────────────────
          Expanded(
            child: LayoutBuilder(builder: (context, constraints) {
              final wide = constraints.maxWidth > 860;
              if (wide) {
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 240,
                      child: Padding(
                        padding: const EdgeInsets.only(left: 16, bottom: 16),
                        child: _SideNav(
                          sections: _sections,
                          selected: _selected,
                          onSelect: (i) => setState(() => _selected = i),
                        ),
                      ),
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.only(right: 16, bottom: 16),
                        child: _content(),
                      ),
                    ),
                  ],
                );
              }
              return Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: _TopChips(
                      sections: _sections,
                      selected: _selected,
                      onSelect: (i) => setState(() => _selected = i),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                      child: _content(),
                    ),
                  ),
                ],
              );
            }),
          ),
        ],
      ),
    );
  }

  Widget _content() {
    final projectId = ref.watch(currentProjectIdProvider);
    switch (_selected) {
      case 0:
        return _BlogTab(projectId: projectId);
      case 1:
        return FormsTab(projectId: projectId);
      case 2:
        return CommentsTab(projectId: projectId);
      case 3:
        return PagesTab(projectId: projectId);
      case 4:
        return MediaTab(projectId: projectId);
      default:
        return const SizedBox.shrink();
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Section model
// ─────────────────────────────────────────────────────────────────────────────

class _CmsSection {
  const _CmsSection(
      this.label, this.icon, this.selectedIcon, this.desc, this.color);
  final String label;
  final IconData icon;
  final IconData selectedIcon;
  final String desc;
  final Color color;
}

// ─────────────────────────────────────────────────────────────────────────────
// Side navigation (wide)
// ─────────────────────────────────────────────────────────────────────────────

class _SideNav extends StatelessWidget {
  const _SideNav(
      {required this.sections, required this.selected, required this.onSelect});
  final List<_CmsSection> sections;
  final int selected;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            for (var i = 0; i < sections.length; i++) ...[
              _NavItem(
                section: sections[i],
                selected: selected == i,
                onTap: () => onSelect(i),
              ),
              if (i < sections.length - 1) const SizedBox(height: 4),
            ],
          ],
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem(
      {required this.section, required this.selected, required this.onTap});
  final _CmsSection section;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: selected
              ? section.color.withValues(alpha: 0.10)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: selected
                    ? section.color
                    : section.color.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                selected ? section.selectedIcon : section.icon,
                color: selected ? Colors.white : section.color,
                size: 18,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(section.label,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: selected ? section.color : AppColors.textPrimary,
                        fontSize: 14,
                      )),
                  Text(section.desc,
                      style: const TextStyle(
                          fontSize: 11, color: AppColors.textSecondary),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Top chips (compact)
// ─────────────────────────────────────────────────────────────────────────────

class _TopChips extends StatelessWidget {
  const _TopChips(
      {required this.sections, required this.selected, required this.onSelect});
  final List<_CmsSection> sections;
  final int selected;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 46,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: sections.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, i) {
          final s = sections[i];
          final isSel = selected == i;
          return GestureDetector(
            onTap: () => onSelect(i),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 160),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: isSel ? s.color : AppColors.surface,
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: isSel ? s.color : AppColors.border),
              ),
              child: Row(
                children: [
                  Icon(s.icon, size: 16, color: isSel ? Colors.white : s.color),
                  const SizedBox(width: 6),
                  Text(s.label,
                      style: TextStyle(
                          fontWeight: FontWeight.w600,
                          color: isSel ? Colors.white : AppColors.textPrimary,
                          fontSize: 13)),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Stats strip
// ─────────────────────────────────────────────────────────────────────────────

class _StatsRow extends ConsumerWidget {
  const _StatsRow({required this.projectId});
  final String? projectId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return LayoutBuilder(builder: (context, constraints) {
      final columns = constraints.maxWidth > 900
          ? 5
          : constraints.maxWidth > 600
              ? 3
              : 2;
      return GridView.count(
        crossAxisCount: columns,
        crossAxisSpacing: 10,
        mainAxisSpacing: 10,
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        childAspectRatio: 2.4,
        children: const [
          _MiniStat(
              icon: Icons.article_outlined,
              label: 'Articles',
              value: '—',
              color: AppColors.skyBlue),
          _MiniStat(
              icon: Icons.dynamic_form_outlined,
              label: 'Formulaires',
              value: '—',
              color: Color(0xFF10B981)),
          _MiniStat(
              icon: Icons.comment_outlined,
              label: 'Commentaires',
              value: '—',
              color: Color(0xFFF59E0B)),
          _MiniStat(
              icon: Icons.web_outlined,
              label: 'Pages',
              value: '—',
              color: Color(0xFF0EA5E9)),
          _MiniStat(
              icon: Icons.image_outlined,
              label: 'Médias',
              value: '—',
              color: Color(0xFF22D3EE)),
        ],
      );
    });
  }
}

class _MiniStat extends StatelessWidget {
  const _MiniStat(
      {required this.icon,
      required this.label,
      required this.value,
      required this.color});
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(9)),
              child: Icon(icon, color: color, size: 17),
            ),
            const SizedBox(width: 9),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(value,
                      style: const TextStyle(
                          fontSize: 18, fontWeight: FontWeight.w800)),
                  Text(label,
                      style: const TextStyle(
                          fontSize: 10, color: AppColors.textSecondary)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// ONGLET 1 — Blog (connecté à l'API projet)
// ─────────────────────────────────────────────────────────────────────────────

class _BlogTab extends ConsumerStatefulWidget {
  const _BlogTab({required this.projectId});
  final String? projectId;

  @override
  ConsumerState<_BlogTab> createState() => _BlogTabState();
}

class _BlogTabState extends ConsumerState<_BlogTab> {
  String? _selectedId;
  final _titleCtrl = TextEditingController();
  final _markdownCtrl = TextEditingController();
  bool _saving = false;
  String _filter = 'all';

  @override
  void dispose() {
    _titleCtrl.dispose();
    _markdownCtrl.dispose();
    super.dispose();
  }

  void _selectArticle(CmsArticle article) {
    setState(() {
      _selectedId = article.id;
      _titleCtrl.text = article.title;
      _markdownCtrl.text = article.markdown;
    });
  }

  Future<void> _create() async {
    final pid = widget.projectId;
    if (pid == null) return;
    final a = await ref.read(cmsArticleControllerProvider).create(pid);
    _selectArticle(a);
    if (mounted) NotificationService.success(context, 'Article créé');
  }

  Future<void> _save(String status) async {
    final pid = widget.projectId;
    final aid = _selectedId;
    if (pid == null || aid == null) return;
    setState(() => _saving = true);
    try {
      final a = await ref.read(cmsArticleControllerProvider).save(pid, aid,
          title: _titleCtrl.text.trim().isEmpty
              ? 'Article sans titre'
              : _titleCtrl.text.trim(),
          markdown: _markdownCtrl.text,
          status: status);
      _selectArticle(a);
      if (mounted)
        NotificationService.success(
            context,
            status == 'published'
                ? 'Article publié ✓'
                : 'Brouillon enregistré ✓');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _delete() async {
    final pid = widget.projectId;
    final aid = _selectedId;
    if (pid == null || aid == null) return;
    await ref.read(cmsArticleControllerProvider).delete(pid, aid);
    setState(() {
      _selectedId = null;
      _titleCtrl.clear();
      _markdownCtrl.clear();
    });
    if (mounted) NotificationService.error(context, 'Article supprimé');
  }

  @override
  Widget build(BuildContext context) {
    if (widget.projectId == null) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(40),
          child: Center(child: Text('Aucun site actif.')),
        ),
      );
    }
    return ref.watch(cmsArticlesProvider(widget.projectId!)).when(
          loading: () => const Card(
              child: Padding(
                  padding: EdgeInsets.all(40),
                  child: Center(child: CircularProgressIndicator()))),
          error: (error, _) => Card(
              child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text('Erreur : $error',
                      style: const TextStyle(color: AppColors.danger)))),
          data: (all) {
            final filtered = _filter == 'all'
                ? all
                : all.where((a) => a.status.name == _filter).toList();

            // Auto-select first if none
            if (_selectedId == null && all.isNotEmpty) {
              WidgetsBinding.instance.addPostFrameCallback((_) {
                _selectArticle(all.first);
              });
            }

            return LayoutBuilder(builder: (ctx, constraints) {
              final wide = constraints.maxWidth > 740;
              final list = _ArticlesList(
                articles: filtered,
                allCount: all.length,
                publishedCount: all.where((a) => a.isPublished).length,
                draftCount:
                    all.where((a) => a.status == ArticleStatus.draft).length,
                selectedId: _selectedId,
                filter: _filter,
                onFilterChange: (f) => setState(() => _filter = f),
                onSelect: _selectArticle,
                onCreate: _create,
              );
              final editor = _ArticleEditor(
                hasSelection: _selectedId != null,
                titleController: _titleCtrl,
                markdownController: _markdownCtrl,
                saving: _saving,
                onPublish: () => _save('published'),
                onDraft: () => _save('draft'),
                onDelete: () => showConfirmDialog(
                  context,
                  title: 'Supprimer l\'article',
                  message: 'Cette action est irréversible.',
                  confirmText: 'Supprimer',
                  isDangerous: true,
                  onConfirm: _delete,
                ),
              );
              if (!wide) {
                return SingleChildScrollView(
                  child: Column(children: [
                    list,
                    const SizedBox(height: 16),
                    editor,
                  ]),
                );
              }
              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(width: 300, child: list),
                  const SizedBox(width: 14),
                  Expanded(child: editor),
                ],
              );
            });
          },
        );
  }
}

// ── Articles list ────────────────────────────────────────────────────────────

class _ArticlesList extends StatelessWidget {
  const _ArticlesList({
    required this.articles,
    required this.allCount,
    required this.publishedCount,
    required this.draftCount,
    required this.selectedId,
    required this.filter,
    required this.onFilterChange,
    required this.onSelect,
    required this.onCreate,
  });

  final List<CmsArticle> articles;
  final int allCount, publishedCount, draftCount;
  final String? selectedId;
  final String filter;
  final ValueChanged<String> onFilterChange;
  final ValueChanged<CmsArticle> onSelect;
  final VoidCallback onCreate;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text('Articles de blog',
                      style:
                          TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
                ),
                FilledButton.icon(
                  onPressed: onCreate,
                  icon: const Icon(Icons.add, size: 16),
                  label: const Text('Nouvel article'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // Filter chips
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(children: [
                _FilterChip(
                    label: 'Tous',
                    count: allCount,
                    selected: filter == 'all',
                    onTap: () => onFilterChange('all')),
                const SizedBox(width: 8),
                _FilterChip(
                    label: 'Publiés',
                    count: publishedCount,
                    selected: filter == 'published',
                    onTap: () => onFilterChange('published')),
                const SizedBox(width: 8),
                _FilterChip(
                    label: 'Brouillons',
                    count: draftCount,
                    selected: filter == 'draft',
                    onTap: () => onFilterChange('draft')),
              ]),
            ),
            const SizedBox(height: 12),
            if (articles.isEmpty)
              const Padding(
                padding: EdgeInsets.all(20),
                child: Center(
                    child: Text('Aucun article.',
                        style: TextStyle(color: AppColors.textSecondary))),
              )
            else
              for (final article in articles)
                Builder(builder: (context) {
                  final isSelected = article.id == selectedId;
                  final statusColor = article.isPublished
                      ? const Color(0xFF10B981)
                      : AppColors.textSecondary;
                  return GestureDetector(
                    onTap: () => onSelect(article),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 140),
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? AppColors.skyBlue.withValues(alpha: 0.08)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: isSelected
                              ? AppColors.skyBlue.withValues(alpha: 0.40)
                              : AppColors.border,
                        ),
                      ),
                      child: Row(children: [
                        Icon(
                          article.isPublished ? Icons.public : Icons.edit_note,
                          color: statusColor,
                          size: 20,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(article.title,
                                  style: TextStyle(
                                      fontWeight: FontWeight.w600,
                                      fontSize: 13,
                                      color: isSelected
                                          ? AppColors.skyBlue
                                          : AppColors.textPrimary),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis),
                              const SizedBox(height: 2),
                              Text(article.isPublished ? 'Publié' : 'Brouillon',
                                  style: TextStyle(
                                      fontSize: 11, color: statusColor)),
                            ],
                          ),
                        ),
                      ]),
                    ),
                  );
                }),
          ],
        ),
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip(
      {required this.label,
      required this.count,
      required this.selected,
      required this.onTap});
  final String label;
  final int count;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 140),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: selected ? AppColors.skyBlue : AppColors.background,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
              color: selected ? AppColors.skyBlue : AppColors.border),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Text(label,
              style: TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 12,
                  color: selected ? Colors.white : AppColors.textPrimary)),
          const SizedBox(width: 5),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
            decoration: BoxDecoration(
              color: selected
                  ? Colors.white.withValues(alpha: 0.25)
                  : AppColors.skyBlueLight,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text('$count',
                style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    color: selected ? Colors.white : AppColors.skyBlueDark)),
          ),
        ]),
      ),
    );
  }
}

// ── Article editor ───────────────────────────────────────────────────────────

class _ArticleEditor extends StatelessWidget {
  const _ArticleEditor({
    required this.hasSelection,
    required this.titleController,
    required this.markdownController,
    required this.saving,
    required this.onPublish,
    required this.onDraft,
    required this.onDelete,
  });

  final bool hasSelection;
  final TextEditingController titleController;
  final TextEditingController markdownController;
  final bool saving;
  final VoidCallback onPublish;
  final VoidCallback onDraft;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (!hasSelection)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(48),
                  child: Column(
                    children: [
                      Icon(Icons.article_outlined,
                          size: 48, color: AppColors.textSecondary),
                      SizedBox(height: 12),
                      Text('Sélectionne un article ou crée-en un nouveau.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: AppColors.textSecondary)),
                    ],
                  ),
                ),
              )
            else ...[
              Text('Édition de l\'article',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 16),
              TextField(
                controller: titleController,
                style:
                    const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                decoration: const InputDecoration(
                    labelText: 'Titre', hintText: 'Titre de l\'article'),
              ),
              const SizedBox(height: 14),
              TextField(
                controller: markdownController,
                maxLines: 16,
                style: const TextStyle(fontFamily: 'monospace', fontSize: 13),
                decoration: const InputDecoration(
                  labelText: 'Contenu (Markdown)',
                  hintText: '# Titre\n\nÉcris ton article en Markdown...',
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 18),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: [
                  FilledButton.icon(
                    onPressed: saving ? null : onPublish,
                    icon: saving
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white))
                        : const Icon(Icons.public, size: 18),
                    label: const Text('Publier'),
                  ),
                  OutlinedButton.icon(
                    onPressed: saving ? null : onDraft,
                    icon: const Icon(Icons.drafts_outlined, size: 18),
                    label: const Text('Brouillon'),
                  ),
                  OutlinedButton.icon(
                    onPressed: saving ? null : onDelete,
                    style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.danger,
                        side: const BorderSide(color: AppColors.danger)),
                    icon: const Icon(Icons.delete_outline, size: 18),
                    label: const Text('Supprimer'),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Widget générique — état vide propre
// ─────────────────────────────────────────────────────────────────────────────

class _ComingSoonTab extends StatelessWidget {
  const _ComingSoonTab({
    required this.icon,
    required this.color,
    required this.title,
    required this.description,
  });

  final IconData icon;
  final Color color;
  final String title;
  final String description;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 56, horizontal: 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(22),
              ),
              child: Icon(icon, color: color, size: 34),
            ),
            const SizedBox(height: 20),
            Text(title,
                style: Theme.of(context)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.w700)),
            const SizedBox(height: 10),
            Text(
              description,
              textAlign: TextAlign.center,
              style: const TextStyle(
                  color: AppColors.textSecondary, fontSize: 13, height: 1.55),
            ),
          ],
        ),
      ),
    );
  }
}
