import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../../widgets/dialogs.dart';
import '../../widgets/notifications.dart';
import '../../widgets/page_scaffold.dart';
import '../projects/project_workspace_state.dart';

class CmsPage extends ConsumerStatefulWidget {
  const CmsPage({super.key});

  @override
  ConsumerState<CmsPage> createState() => _CmsPageState();
}

class _CmsPageState extends ConsumerState<CmsPage> {
  late Future<List<dynamic>> _articlesFuture;
  String? _selectedArticleId;
  final _titleController = TextEditingController();
  final _markdownController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _articlesFuture = _loadArticles();
  }

  @override
  void dispose() {
    _titleController.dispose();
    _markdownController.dispose();
    super.dispose();
  }

  Future<List<dynamic>> _loadArticles() async {
    final projectId = ref.read(currentProjectIdProvider);
    if (projectId == null || projectId.isEmpty) return [];
    return ref.read(apiClientProvider).articles(projectId);
  }

  void _reloadArticles() {
    setState(() {
      _articlesFuture = _loadArticles();
    });
  }

  void _selectArticle(Map<String, dynamic> article) {
    setState(() {
      _selectedArticleId = article['id']?.toString();
      _titleController.text = article['title']?.toString() ?? '';
      _markdownController.text = article['markdown']?.toString() ?? '';
    });
  }

  Future<void> _createArticle() async {
    final projectId = ref.read(currentProjectIdProvider);
    if (projectId == null || projectId.isEmpty) {
      NotificationService.error(context, 'Aucun projet sélectionné');
      return;
    }
    final article = await ref.read(apiClientProvider).createArticle(projectId, 'Nouvel article', '# Nouvel article\n\nCommence à écrire ici.', 'draft');
    _selectArticle(article);
    _reloadArticles();
    if (mounted) NotificationService.success(context, 'Article créé');
  }

  Future<void> _saveArticle(String status) async {
    final projectId = ref.read(currentProjectIdProvider);
    final articleId = _selectedArticleId;
    if (projectId == null || projectId.isEmpty || articleId == null) return;
    final article = await ref.read(apiClientProvider).updateArticle(
          projectId,
          articleId,
          title: _titleController.text.trim().isEmpty ? 'Article sans titre' : _titleController.text.trim(),
          markdown: _markdownController.text,
          status: status,
        );
    _selectArticle(article);
    _reloadArticles();
    if (mounted) NotificationService.success(context, status == 'published' ? 'Article publié' : 'Article enregistré');
  }

  Future<void> _deleteArticle() async {
    final projectId = ref.read(currentProjectIdProvider);
    final articleId = _selectedArticleId;
    if (projectId == null || projectId.isEmpty || articleId == null) return;
    await ref.read(apiClientProvider).deleteArticle(projectId, articleId);
    setState(() {
      _selectedArticleId = null;
      _titleController.clear();
      _markdownController.clear();
    });
    _reloadArticles();
    if (mounted) NotificationService.error(context, 'Article supprimé');
  }

  @override
  Widget build(BuildContext context) {
    final projectId = ref.watch(currentProjectIdProvider);
    return PageScaffold(
      title: 'CMS & Blog',
      action: FilledButton.icon(
        onPressed: projectId == null ? null : _createArticle,
        icon: const Icon(Icons.add),
        label: const Text('Article'),
      ),
      children: [
        if (projectId == null)
          const Card(child: Padding(padding: EdgeInsets.all(32), child: Center(child: Text('Ouvre un projet pour gérer ses articles.'))))
        else
          FutureBuilder<List<dynamic>>(
            future: _articlesFuture,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Card(child: Padding(padding: EdgeInsets.all(40), child: Center(child: CircularProgressIndicator())));
              }
              if (snapshot.hasError) {
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text('Erreur CMS : ${snapshot.error}', style: const TextStyle(color: AppColors.danger)),
                  ),
                );
              }
              final articles = snapshot.data ?? [];
              Map<String, dynamic>? selected;
              for (final item in articles) {
                final article = Map<String, dynamic>.from(item as Map);
                if (article['id']?.toString() == _selectedArticleId) {
                  selected = article;
                  break;
                }
              }
              if (selected != null && _titleController.text.isEmpty && _markdownController.text.isEmpty) {
                _selectArticle(selected);
              }
              return LayoutBuilder(builder: (context, constraints) {
                final wide = constraints.maxWidth > 820;
                final editor = _ArticleEditor(
                  hasSelection: _selectedArticleId != null,
                  titleController: _titleController,
                  markdownController: _markdownController,
                  onPublish: () => _saveArticle('published'),
                  onDraft: () => _saveArticle('draft'),
                  onDelete: () => showConfirmDialog(
                    context,
                    title: 'Supprimer l’article',
                    message: 'Cette action est irréversible.',
                    confirmText: 'Supprimer',
                    isDangerous: true,
                    onConfirm: _deleteArticle,
                  ),
                );
                final list = _ArticlesList(
                  articles: articles,
                  selectedArticleId: _selectedArticleId,
                  onSelect: (article) => _selectArticle(article),
                );
                if (!wide) return Column(children: [list, const SizedBox(height: 16), editor]);
                return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [SizedBox(width: 320, child: list), const SizedBox(width: 16), Expanded(child: editor)]);
              });
            },
          ),
      ],
    );
  }
}

class _ArticlesList extends StatelessWidget {
  const _ArticlesList({required this.articles, required this.selectedArticleId, required this.onSelect});

  final List<dynamic> articles;
  final String? selectedArticleId;
  final ValueChanged<Map<String, dynamic>> onSelect;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          if (articles.isEmpty)
            const Padding(padding: EdgeInsets.all(24), child: Text('Aucun article pour ce projet.'))
          else
            for (final item in articles)
              Builder(builder: (context) {
                final article = Map<String, dynamic>.from(item as Map);
                final status = article['status']?.toString() ?? 'draft';
                final selected = article['id']?.toString() == selectedArticleId;
                return ListTile(
                  selected: selected,
                  leading: Icon(status == 'published' ? Icons.public : Icons.edit_note, color: status == 'published' ? const Color(0xFF10B981) : AppColors.skyBlue),
                  title: Text(article['title']?.toString() ?? 'Article'),
                  subtitle: Text(status == 'published' ? 'Publié' : 'Brouillon'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => onSelect(article),
                );
              }),
        ],
      ),
    );
  }
}

class _ArticleEditor extends StatelessWidget {
  const _ArticleEditor({
    required this.hasSelection,
    required this.titleController,
    required this.markdownController,
    required this.onPublish,
    required this.onDraft,
    required this.onDelete,
  });

  final bool hasSelection;
  final TextEditingController titleController;
  final TextEditingController markdownController;
  final VoidCallback onPublish;
  final VoidCallback onDraft;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (!hasSelection)
              const Center(child: Padding(padding: EdgeInsets.all(40), child: Text('Aucun article sélectionné')))
            else ...[
              Text('Édition article', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 16),
              TextField(controller: titleController, decoration: const InputDecoration(labelText: 'Titre')),
              const SizedBox(height: 12),
              TextField(controller: markdownController, maxLines: 12, decoration: const InputDecoration(labelText: 'Markdown')),
              const SizedBox(height: 16),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  FilledButton.icon(onPressed: onPublish, icon: const Icon(Icons.publish), label: const Text('Publier')),
                  OutlinedButton.icon(onPressed: onDraft, icon: const Icon(Icons.drafts_outlined), label: const Text('Brouillon')),
                  OutlinedButton.icon(onPressed: onDelete, icon: const Icon(Icons.delete_outline), label: const Text('Supprimer')),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
