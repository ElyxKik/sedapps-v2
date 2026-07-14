import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme.dart';
import '../data/cms_repository.dart';
import '../domain/cms_models.dart';

class FormsTab extends ConsumerWidget {
  const FormsTab({required this.projectId, super.key});
  final String? projectId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final id = projectId;
    if (id == null) return const CmsEmptyProject();
    final formsState = ref.watch(cmsFormsProvider(id));
    final submissionsState = ref.watch(cmsSubmissionsProvider(id));
    if (formsState.isLoading || submissionsState.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (formsState.hasError || submissionsState.hasError) {
      return CmsError(message: '${formsState.error ?? submissionsState.error}');
    }
    final forms = formsState.value ?? const <CmsForm>[];
    final submissions = submissionsState.value ?? const <FormSubmission>[];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('Formulaires (${forms.length})',
              style: Theme.of(context).textTheme.titleLarge),
          for (final form in forms)
            ListTile(
              leading: const Icon(Icons.dynamic_form_outlined),
              title: Text(form.name),
              subtitle: Text('${form.submissionCount} soumission(s)'),
            ),
          const Divider(),
          Text('Messages reçus (${submissions.length})'),
          for (final submission in submissions.take(20))
            ListTile(
              leading: const Icon(Icons.mail_outline),
              title: Text(submission.formName),
              subtitle: Text(submission.data.values.join(' · ')),
            ),
        ]),
      ),
    );
  }
}

class CommentsTab extends ConsumerWidget {
  const CommentsTab({required this.projectId, super.key});
  final String? projectId;

  Future<void> _update(WidgetRef ref, String commentId, String status) async {
    final id = projectId!;
    await ref
        .read(cmsRepositoryProvider)
        .updateCommentStatus(id, commentId, status);
    ref.invalidate(cmsCommentsProvider(id));
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final id = projectId;
    if (id == null) return const CmsEmptyProject();
    return ref.watch(cmsCommentsProvider(id)).when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => CmsError(message: '$error'),
          data: (comments) => Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Commentaires (${comments.length})',
                        style: Theme.of(context).textTheme.titleLarge),
                    if (comments.isEmpty)
                      const Text('Aucun commentaire à modérer.'),
                    for (final comment in comments)
                      ListTile(
                        leading: const Icon(Icons.comment_outlined),
                        title: Text(comment.authorName),
                        subtitle: Text(comment.content),
                        trailing: PopupMenuButton<String>(
                          initialValue: comment.status,
                          onSelected: (status) =>
                              _update(ref, comment.id, status),
                          itemBuilder: (_) => const [
                            PopupMenuItem(
                                value: 'approved', child: Text('Approuver')),
                            PopupMenuItem(
                                value: 'rejected', child: Text('Rejeter')),
                            PopupMenuItem(value: 'spam', child: Text('Spam')),
                          ],
                        ),
                      ),
                  ]),
            ),
          ),
        );
  }
}

class MediaTab extends ConsumerWidget {
  const MediaTab({required this.projectId, super.key});
  final String? projectId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final id = projectId;
    if (id == null) return const CmsEmptyProject();
    return ref.watch(cmsMediaProvider(id)).when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => CmsError(message: '$error'),
          data: (media) => Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Médiathèque (${media.length})',
                        style: Theme.of(context).textTheme.titleLarge),
                    if (media.isEmpty) const Text('Aucun média enregistré.'),
                    for (final item in media)
                      ListTile(
                        leading: const Icon(Icons.image_outlined),
                        title: Text(item.filename),
                        subtitle:
                            Text('${item.mime} · ${item.sizeBytes} octets'),
                      ),
                  ]),
            ),
          ),
        );
  }
}

class PagesTab extends ConsumerWidget {
  const PagesTab({required this.projectId, super.key});
  final String? projectId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final id = projectId;
    if (id == null) return const CmsEmptyProject();
    return ref.watch(cmsPagesProvider(id)).when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => CmsError(message: '$error'),
          data: (pages) => Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Pages (${pages.length})',
                        style: Theme.of(context).textTheme.titleLarge),
                    for (final page in pages)
                      ListTile(
                        leading: const Icon(Icons.web_outlined),
                        title: Text(page.slug),
                        subtitle: Text('Composant ${page.type} · ${page.id}'),
                      ),
                  ]),
            ),
          ),
        );
  }
}

class CmsEmptyProject extends StatelessWidget {
  const CmsEmptyProject({super.key});
  @override
  Widget build(BuildContext context) => const Card(
      child: Padding(
          padding: EdgeInsets.all(32), child: Text('Aucun site actif.')));
}

class CmsError extends StatelessWidget {
  const CmsError({required this.message, super.key});
  final String message;
  @override
  Widget build(BuildContext context) => Card(
      child: Padding(
          padding: const EdgeInsets.all(24),
          child:
              Text(message, style: const TextStyle(color: AppColors.danger))));
}
