import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../../widgets/dialogs.dart';
import '../../widgets/notifications.dart';
import '../projects/project_workspace_state.dart';

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
    _CmsSection('Blog', Icons.article_outlined, Icons.article_rounded,
        'Articles & catégories', AppColors.skyBlue),
    _CmsSection('Formulaires', Icons.dynamic_form_outlined,
        Icons.dynamic_form_rounded, 'Contact, devis, newsletter',
        Color(0xFF10B981)),
    _CmsSection('Commentaires', Icons.comment_outlined, Icons.comment_rounded,
        'Modération', Color(0xFFF59E0B)),
    _CmsSection('Pages', Icons.web_outlined, Icons.web_rounded,
        'À propos, Contact, Légal', Color(0xFF6366F1)),
    _CmsSection('Médias', Icons.image_outlined, Icons.image_rounded,
        'Images, vidéos, fichiers', Color(0xFFEC4899)),
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
        return const _FormsTab();
      case 2:
        return const _CommentsTab();
      case 3:
        return const _PagesTab();
      case 4:
        return const _MediaTab();
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
      {required this.sections,
      required this.selected,
      required this.onSelect});
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
                        color:
                            selected ? section.color : AppColors.textPrimary,
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
      {required this.sections,
      required this.selected,
      required this.onSelect});
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
              padding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: isSel ? s.color : AppColors.surface,
                borderRadius: BorderRadius.circular(30),
                border:
                    Border.all(color: isSel ? s.color : AppColors.border),
              ),
              child: Row(
                children: [
                  Icon(s.icon,
                      size: 16,
                      color: isSel ? Colors.white : s.color),
                  const SizedBox(width: 6),
                  Text(s.label,
                      style: TextStyle(
                          fontWeight: FontWeight.w600,
                          color: isSel
                              ? Colors.white
                              : AppColors.textPrimary,
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
              value: '4',
              color: Color(0xFF10B981)),
          _MiniStat(
              icon: Icons.comment_outlined,
              label: 'Commentaires',
              value: '23',
              color: Color(0xFFF59E0B)),
          _MiniStat(
              icon: Icons.web_outlined,
              label: 'Pages',
              value: '8',
              color: Color(0xFF6366F1)),
          _MiniStat(
              icon: Icons.image_outlined,
              label: 'Médias',
              value: '47',
              color: Color(0xFFEC4899)),
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
  late Future<List<dynamic>> _future;
  String? _selectedId;
  final _titleCtrl = TextEditingController();
  final _markdownCtrl = TextEditingController();
  bool _saving = false;
  String _filter = 'all';

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _markdownCtrl.dispose();
    super.dispose();
  }

  Future<List<dynamic>> _load() async {
    final pid = widget.projectId;
    if (pid == null || pid.isEmpty) return [];
    return ref.read(apiClientProvider).articles(pid);
  }

  void _reload() => setState(() => _future = _load());

  void _selectArticle(Map<String, dynamic> a) {
    setState(() {
      _selectedId = a['id']?.toString();
      _titleCtrl.text = a['title']?.toString() ?? '';
      _markdownCtrl.text = a['markdown']?.toString() ?? '';
    });
  }

  Future<void> _create() async {
    final pid = widget.projectId;
    if (pid == null) return;
    final a = await ref
        .read(apiClientProvider)
        .createArticle(pid, 'Nouvel article',
            '# Nouvel article\n\nCommence à écrire ici.', 'draft');
    _selectArticle(a);
    _reload();
    if (mounted) NotificationService.success(context, 'Article créé');
  }

  Future<void> _save(String status) async {
    final pid = widget.projectId;
    final aid = _selectedId;
    if (pid == null || aid == null) return;
    setState(() => _saving = true);
    try {
      final a = await ref.read(apiClientProvider).updateArticle(pid, aid,
          title: _titleCtrl.text.trim().isEmpty
              ? 'Article sans titre'
              : _titleCtrl.text.trim(),
          markdown: _markdownCtrl.text,
          status: status);
      _selectArticle(a);
      _reload();
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
    await ref.read(apiClientProvider).deleteArticle(pid, aid);
    setState(() {
      _selectedId = null;
      _titleCtrl.clear();
      _markdownCtrl.clear();
    });
    _reload();
    if (mounted) NotificationService.error(context, 'Article supprimé');
  }

  @override
  Widget build(BuildContext context) {
    if (widget.projectId == null) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(40),
          child: Center(child: Text('Aucun projet actif.')),
        ),
      );
    }
    return FutureBuilder<List<dynamic>>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Card(
              child: Padding(
                  padding: EdgeInsets.all(40),
                  child: Center(child: CircularProgressIndicator())));
        }
        if (snap.hasError) {
          return Card(
              child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text('Erreur : ${snap.error}',
                      style: const TextStyle(color: AppColors.danger))));
        }
        final all = snap.data ?? [];
        final filtered = _filter == 'all'
            ? all
            : all
                .where((a) =>
                    (a as Map)['status']?.toString() == _filter)
                .toList();

        // Auto-select first if none
        if (_selectedId == null && all.isNotEmpty) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            _selectArticle(Map<String, dynamic>.from(all.first as Map));
          });
        }

        Map<String, dynamic>? selected;
        for (final a in all) {
          if ((a as Map)['id']?.toString() == _selectedId) {
            selected = Map<String, dynamic>.from(a);
            break;
          }
        }

        return LayoutBuilder(builder: (ctx, constraints) {
          final wide = constraints.maxWidth > 740;
          final list = _ArticlesList(
            articles: filtered,
            allCount: all.length,
            publishedCount: all
                .where((a) =>
                    (a as Map)['status']?.toString() == 'published')
                .length,
            draftCount: all
                .where(
                    (a) => (a as Map)['status']?.toString() == 'draft')
                .length,
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

  final List<dynamic> articles;
  final int allCount, publishedCount, draftCount;
  final String? selectedId;
  final String filter;
  final ValueChanged<String> onFilterChange;
  final ValueChanged<Map<String, dynamic>> onSelect;
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
                      style: TextStyle(
                          fontSize: 15, fontWeight: FontWeight.w800)),
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
              for (final item in articles)
                Builder(builder: (context) {
                  final a = Map<String, dynamic>.from(item as Map);
                  final status = a['status']?.toString() ?? 'draft';
                  final isSelected = a['id']?.toString() == selectedId;
                  final statusColor = status == 'published'
                      ? const Color(0xFF10B981)
                      : AppColors.textSecondary;
                  return GestureDetector(
                    onTap: () => onSelect(a),
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
                          status == 'published'
                              ? Icons.public
                              : Icons.edit_note,
                          color: statusColor,
                          size: 20,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(a['title']?.toString() ?? 'Article',
                                  style: TextStyle(
                                      fontWeight: FontWeight.w600,
                                      fontSize: 13,
                                      color: isSelected
                                          ? AppColors.skyBlue
                                          : AppColors.textPrimary),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis),
                              const SizedBox(height: 2),
                              Text(
                                  status == 'published'
                                      ? 'Publié'
                                      : 'Brouillon',
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
                  color:
                      selected ? Colors.white : AppColors.textPrimary)),
          const SizedBox(width: 5),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
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
                    color:
                        selected ? Colors.white : AppColors.skyBlueDark)),
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
                          style:
                              TextStyle(color: AppColors.textSecondary)),
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
                  hintText:
                      '# Titre\n\nÉcris ton article en Markdown...',
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
// ONGLET 2 — Formulaires (identique au CmsHubPage)
// ─────────────────────────────────────────────────────────────────────────────

class _FormsTab extends StatelessWidget {
  const _FormsTab();

  static const _forms = [
    {'name': 'Formulaire Contact', 'submissions': 47, 'fields': 5, 'active': true},
    {'name': 'Demande de devis', 'submissions': 23, 'fields': 8, 'active': true},
    {'name': 'Inscription newsletter', 'submissions': 156, 'fields': 2, 'active': true},
    {'name': 'Candidature spontanée', 'submissions': 4, 'fields': 6, 'active': false},
  ];

  static const _recent = [
    {'form': 'Contact', 'email': 'jean.dupont@example.com', 'date': 'Il y a 2h', 'name': 'Jean Dupont'},
    {'form': 'Devis', 'email': 'marie@startup.fr', 'date': 'Il y a 5h', 'name': 'Marie Lambert'},
    {'form': 'Newsletter', 'email': 'pierre.martin@gmail.com', 'date': 'Hier', 'name': 'Pierre Martin'},
    {'form': 'Contact', 'email': 'sophie@agence.com', 'date': 'Hier', 'name': 'Sophie Bernard'},
  ];

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              const Expanded(child: Text('Formulaires', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800))),
              FilledButton.icon(onPressed: () {}, icon: const Icon(Icons.add, size: 16), label: const Text('Nouveau formulaire')),
            ]),
            const SizedBox(height: 12),
            for (final f in _forms) _FormRow(form: f),
          ]),
        ),
      ),
      const SizedBox(height: 16),
      Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Soumissions récentes', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
            const SizedBox(height: 12),
            for (final s in _recent) _SubmissionRow(submission: s),
          ]),
        ),
      ),
    ]);
  }
}

class _FormRow extends StatelessWidget {
  const _FormRow({required this.form});
  final Map<String, dynamic> form;

  @override
  Widget build(BuildContext context) {
    final active = form['active'] as bool;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(border: Border.all(color: AppColors.border), borderRadius: BorderRadius.circular(12)),
      child: Row(children: [
        Container(
          width: 40, height: 40,
          decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFF10B981), Color(0xFF34D399)]), borderRadius: BorderRadius.circular(10)),
          child: const Icon(Icons.dynamic_form, color: Colors.white, size: 20),
        ),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(form['name'] as String, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          const SizedBox(height: 3),
          Text('${form['fields']} champs · ${form['submissions']} soumissions',
              style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
        ])),
        Switch(value: active, onChanged: (_) {}, activeColor: const Color(0xFF10B981)),
        IconButton(icon: const Icon(Icons.more_horiz, size: 18), onPressed: () {}),
      ]),
    );
  }
}

class _SubmissionRow extends StatelessWidget {
  const _SubmissionRow({required this.submission});
  final Map<String, dynamic> submission;

  @override
  Widget build(BuildContext context) {
    final initial = (submission['name'] as String).substring(0, 1);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(children: [
        CircleAvatar(
          radius: 17,
          backgroundColor: AppColors.skyBlueLight,
          child: Text(initial, style: const TextStyle(color: AppColors.skyBlueDark, fontWeight: FontWeight.w700)),
        ),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(submission['name'] as String, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
          Text(submission['email'] as String, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
        ])),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          decoration: BoxDecoration(color: AppColors.skyBlueLight, borderRadius: BorderRadius.circular(20)),
          child: Text(submission['form'] as String,
              style: const TextStyle(color: AppColors.skyBlueDark, fontSize: 11, fontWeight: FontWeight.w600)),
        ),
      ]),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// ONGLET 3 — Commentaires
// ─────────────────────────────────────────────────────────────────────────────

class _CommentsTab extends StatelessWidget {
  const _CommentsTab();

  static const _comments = [
    {'author': 'Jean Dupont', 'article': 'Tendances 2026', 'text': 'Super article, très instructif !', 'status': 'approved', 'date': '15 mars'},
    {'author': 'Marie Lambert', 'article': 'Guide responsive', 'text': 'Merci pour les conseils pratiques.', 'status': 'pending', 'date': '14 mars'},
    {'author': 'Paul Martin', 'article': 'SEO en 2026', 'text': 'Excellent contenu, partage ça !', 'status': 'approved', 'date': '13 mars'},
    {'author': 'Sophie B.', 'article': 'IA no-code', 'text': 'Spam promu ici www.xxx.com', 'status': 'spam', 'date': '12 mars'},
  ];

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Modération des commentaires', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
          const SizedBox(height: 14),
          for (final c in _comments) _CommentRow(comment: c),
        ]),
      ),
    );
  }
}

class _CommentRow extends StatelessWidget {
  const _CommentRow({required this.comment});
  final Map<String, dynamic> comment;

  @override
  Widget build(BuildContext context) {
    final status = comment['status'] as String;
    final color = status == 'approved'
        ? const Color(0xFF10B981)
        : status == 'spam'
            ? AppColors.danger
            : const Color(0xFFF59E0B);
    final statusLabel = status == 'approved' ? 'Approuvé' : status == 'spam' ? 'Spam' : 'En attente';
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(border: Border.all(color: AppColors.border), borderRadius: BorderRadius.circular(12)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          CircleAvatar(radius: 16, backgroundColor: AppColors.skyBlueLight,
              child: Text((comment['author'] as String).substring(0, 1),
                  style: const TextStyle(color: AppColors.skyBlueDark, fontWeight: FontWeight.bold, fontSize: 13))),
          const SizedBox(width: 10),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(comment['author'] as String, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
            Text('sur "${comment['article']}" · ${comment['date']}',
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 11)),
          ])),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(20)),
            child: Text(statusLabel, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w700)),
          ),
        ]),
        const SizedBox(height: 8),
        Text(comment['text'] as String, style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
        const SizedBox(height: 8),
        Row(children: [
          TextButton.icon(onPressed: () {}, icon: const Icon(Icons.check, size: 14), label: const Text('Approuver')),
          TextButton.icon(onPressed: () {},
              style: TextButton.styleFrom(foregroundColor: AppColors.danger),
              icon: const Icon(Icons.delete_outline, size: 14), label: const Text('Supprimer')),
        ]),
      ]),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// ONGLET 4 — Pages
// ─────────────────────────────────────────────────────────────────────────────

class _PagesTab extends StatelessWidget {
  const _PagesTab();

  static const _pages = [
    {'title': 'À propos', 'slug': '/about', 'status': 'published', 'lastEdit': '10 mars'},
    {'title': 'Contact', 'slug': '/contact', 'status': 'published', 'lastEdit': '8 mars'},
    {'title': 'Mentions légales', 'slug': '/legal', 'status': 'draft', 'lastEdit': '5 mars'},
    {'title': 'Politique de confidentialité', 'slug': '/privacy', 'status': 'published', 'lastEdit': '5 mars'},
    {'title': 'FAQ', 'slug': '/faq', 'status': 'draft', 'lastEdit': '2 mars'},
  ];

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Expanded(child: Text('Pages statiques', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800))),
            FilledButton.icon(onPressed: () {}, icon: const Icon(Icons.add, size: 16), label: const Text('Nouvelle page')),
          ]),
          const SizedBox(height: 14),
          for (final p in _pages) _PageRow(page: p),
        ]),
      ),
    );
  }
}

class _PageRow extends StatelessWidget {
  const _PageRow({required this.page});
  final Map<String, dynamic> page;

  @override
  Widget build(BuildContext context) {
    final published = page['status'] == 'published';
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(border: Border.all(color: AppColors.border), borderRadius: BorderRadius.circular(12)),
      child: Row(children: [
        Container(
          width: 38, height: 38,
          decoration: BoxDecoration(
            color: (published ? const Color(0xFF6366F1) : AppColors.textSecondary).withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(Icons.web, color: published ? const Color(0xFF6366F1) : AppColors.textSecondary, size: 18),
        ),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(page['title'] as String, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          Text('${page['slug']} · modifié ${page['lastEdit']}',
              style: const TextStyle(color: AppColors.textSecondary, fontSize: 11)),
        ])),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(
            color: (published ? const Color(0xFF10B981) : AppColors.textSecondary).withValues(alpha: 0.10),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(published ? 'Publié' : 'Brouillon',
              style: TextStyle(
                  color: published ? const Color(0xFF10B981) : AppColors.textSecondary,
                  fontSize: 11, fontWeight: FontWeight.w600)),
        ),
        const SizedBox(width: 8),
        IconButton(icon: const Icon(Icons.edit_outlined, size: 18), onPressed: () {}),
      ]),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// ONGLET 5 — Médias
// ─────────────────────────────────────────────────────────────────────────────

class _MediaTab extends StatelessWidget {
  const _MediaTab();

  static const _files = [
    {'name': 'hero-banner.jpg', 'size': '2.4 MB', 'type': 'image', 'date': '15 mars'},
    {'name': 'logo.svg', 'size': '18 KB', 'type': 'svg', 'date': '12 mars'},
    {'name': 'team-photo.jpg', 'size': '3.1 MB', 'type': 'image', 'date': '10 mars'},
    {'name': 'brochure.pdf', 'size': '1.2 MB', 'type': 'pdf', 'date': '8 mars'},
    {'name': 'video-promo.mp4', 'size': '24 MB', 'type': 'video', 'date': '5 mars'},
    {'name': 'about-bg.jpg', 'size': '1.8 MB', 'type': 'image', 'date': '2 mars'},
  ];

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Expanded(child: Text('Médiathèque', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800))),
            FilledButton.icon(
              onPressed: () {},
              icon: const Icon(Icons.upload, size: 16),
              label: const Text('Importer'),
              style: FilledButton.styleFrom(backgroundColor: const Color(0xFFEC4899)),
            ),
          ]),
          const SizedBox(height: 6),
          Text('${_files.length} fichiers · 32.5 MB utilisés',
              style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
          const SizedBox(height: 16),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
              maxCrossAxisExtent: 160,
              mainAxisExtent: 140,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
            ),
            itemCount: _files.length,
            itemBuilder: (_, i) => _MediaCard(file: _files[i]),
          ),
        ]),
      ),
    );
  }
}

class _MediaCard extends StatelessWidget {
  const _MediaCard({required this.file});
  final Map<String, dynamic> file;

  IconData get _icon {
    switch (file['type']) {
      case 'image': return Icons.image_outlined;
      case 'svg': return Icons.auto_awesome_mosaic_outlined;
      case 'pdf': return Icons.picture_as_pdf_outlined;
      case 'video': return Icons.videocam_outlined;
      default: return Icons.insert_drive_file_outlined;
    }
  }

  Color get _color {
    switch (file['type']) {
      case 'image': return const Color(0xFFEC4899);
      case 'svg': return const Color(0xFF6366F1);
      case 'pdf': return const Color(0xFFEF4444);
      case 'video': return const Color(0xFFF59E0B);
      default: return AppColors.textSecondary;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Container(
          width: 52, height: 52,
          decoration: BoxDecoration(color: _color.withValues(alpha: 0.10), borderRadius: BorderRadius.circular(12)),
          child: Icon(_icon, color: _color, size: 26),
        ),
        const SizedBox(height: 8),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Text(file['name'] as String,
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center),
        ),
        const SizedBox(height: 2),
        Text(file['size'] as String,
            style: const TextStyle(fontSize: 10, color: AppColors.textSecondary)),
      ]),
    );
  }
}
