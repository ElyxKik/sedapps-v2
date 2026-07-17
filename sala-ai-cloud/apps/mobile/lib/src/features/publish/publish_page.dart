import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme.dart';
import '../../widgets/notifications.dart';
import '../../widgets/page_scaffold.dart';
import '../projects/project_workspace_state.dart';
import 'data/domains_repository.dart';
import 'data/publishing_repository.dart';
import 'domain/managed_domain.dart';

class PublishPage extends ConsumerStatefulWidget {
  const PublishPage({super.key});

  @override
  ConsumerState<PublishPage> createState() => _PublishPageState();
}

class _PublishPageState extends ConsumerState<PublishPage> {
  final _searchController = TextEditingController();
  DomainSearchResult? _searchResult;
  bool _searching = false;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) return;
    setState(() => _searching = true);
    try {
      final result = await ref.read(domainsRepositoryProvider).search(query);
      if (mounted) setState(() => _searchResult = result);
    } catch (_) {
      if (mounted)
        NotificationService.error(context,
            'Ce nom de domaine est invalide ou la recherche a échoué.');
    } finally {
      if (mounted) setState(() => _searching = false);
    }
  }

  Future<void> _addSearchedDomain() async {
    final result = _searchResult;
    if (result == null || result.available || !result.checked) return;
    try {
      final domain =
          await ref.read(domainsRepositoryProvider).add(result.domain);
      ref.invalidate(managedDomainsProvider);
      if (mounted)
        NotificationService.success(context,
            'Ajoute maintenant le TXT de vérification dans Mes domaines.');
    } catch (_) {
      if (mounted)
        NotificationService.error(
            context, 'Impossible d’ajouter ce domaine pour le moment.');
    }
  }

  Future<void> _selectDomain(ManagedDomain domain) async {
    final projectId = ref.read(currentProjectIdProvider);
    if (projectId == null) return;
    try {
      await ref.read(domainsRepositoryProvider).assign(domain.id, projectId);
      ref.invalidate(managedDomainsProvider);
      ref
          .read(projectWorkspaceProvider.notifier)
          .configurePublishingDomain(domain.name, custom: true);
    } catch (_) {
      if (mounted)
        NotificationService.error(
            context, 'Ce domaine n’a pas pu être lié au projet.');
    }
  }

  Future<void> _createSubdomain(List<ManagedDomain> domains) async {
    final roots = domains.where((d) => !d.isSubdomain).toList();
    if (roots.isEmpty) {
      NotificationService.error(
          context, 'Ajoute d’abord un domaine principal dans Mon compte.');
      return;
    }
    var parent = roots.first;
    final controller = TextEditingController();
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
          builder: (context, setDialogState) => AlertDialog(
                title: const Text('Créer un sous-domaine'),
                content: Column(mainAxisSize: MainAxisSize.min, children: [
                  DropdownButtonFormField<ManagedDomain>(
                    initialValue: parent,
                    decoration:
                        const InputDecoration(labelText: 'Domaine principal'),
                    items: roots
                        .map((d) =>
                            DropdownMenuItem(value: d, child: Text(d.name)))
                        .toList(),
                    onChanged: (value) =>
                        setDialogState(() => parent = value ?? parent),
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: controller,
                    autofocus: true,
                    decoration: InputDecoration(
                        labelText: 'Nom du sous-domaine',
                        hintText: 'boutique',
                        suffixText: '.${parent.name}'),
                  ),
                ]),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(context, false),
                      child: const Text('Annuler')),
                  FilledButton(
                      onPressed: () => Navigator.pop(context, true),
                      child: const Text('Créer et utiliser')),
                ],
              )),
    );
    if (accepted != true || controller.text.trim().isEmpty) return;
    try {
      final domain = await ref
          .read(domainsRepositoryProvider)
          .addSubdomain(parent.id, controller.text.trim().toLowerCase());
      ref.invalidate(managedDomainsProvider);
      await _selectDomain(domain);
    } catch (_) {
      if (mounted)
        NotificationService.error(
            context, 'Ce sous-domaine est invalide ou existe déjà.');
    } finally {
      controller.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    final workspace = ref.watch(projectWorkspaceProvider);
    final publish = workspace.publish;
    final domainsAsync = ref.watch(managedDomainsProvider);
    final domains = domainsAsync.valueOrNull ?? const <ManagedDomain>[];
    final projectId = ref.watch(currentProjectIdProvider);
    final isPublishing =
        publish.status == 'building' || publish.status == 'uploading';

    return PageScaffold(
      title: 'Mise en ligne',
      subtitle:
          'Choisis ton adresse, vérifie la configuration et publie ton site.',
      action: OutlinedButton.icon(
        onPressed: projectId == null ? null : () => _download(projectId),
        icon: const Icon(Icons.download_outlined),
        label: const Text('Télécharger une copie'),
      ),
      children: [
        _StatusHero(publish: publish),
        const SizedBox(height: 24),
        Text('1. Choisis l’adresse de ton site',
            style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),
        LayoutBuilder(builder: (context, constraints) {
          final width = constraints.maxWidth >= 900
              ? (constraints.maxWidth - 32) / 3
              : constraints.maxWidth;
          return Wrap(spacing: 16, runSpacing: 16, children: [
            SizedBox(
                width: width,
                child: _DomainChoice(
                  selected: !publish.customDomainEnabled,
                  icon: Icons.bolt,
                  title: 'Sous-domaine SalaAI',
                  description: 'Inclus, sécurisé et disponible immédiatement.',
                  value: publish.customDomainEnabled
                      ? 'nom-projet.salaai.site'
                      : publish.domain,
                  actionLabel: 'Utiliser cette adresse',
                  onTap: () {
                    final fallback = publish.domain.endsWith('.salaai.site')
                        ? publish.domain
                        : 'nom-projet.salaai.site';
                    ref
                        .read(projectWorkspaceProvider.notifier)
                        .configurePublishingDomain(fallback, custom: false);
                  },
                )),
            SizedBox(
                width: width,
                child: _DomainChoice(
                  selected: publish.customDomainEnabled &&
                      domains.any((d) => d.name == publish.domain),
                  icon: Icons.language,
                  title: 'Un de mes domaines',
                  description:
                      'Utilise un domaine libre ou crée un sous-domaine.',
                  value: domains
                          .where((d) =>
                              d.isAvailableForProject ||
                              d.projectId == projectId)
                          .isEmpty
                      ? 'Aucun domaine disponible'
                      : '${domains.where((d) => d.isAvailableForProject || d.projectId == projectId).length} adresse(s) disponible(s)',
                  actionLabel: 'Choisir',
                  onTap: () => _showDomainPicker(domains, projectId),
                  secondaryLabel: 'Créer un sous-domaine',
                  onSecondary: () => _createSubdomain(domains),
                )),
            SizedBox(
                width: width,
                child: _DomainChoice(
                  selected: false,
                  icon: Icons.travel_explore,
                  title: 'Trouver un domaine',
                  description: 'Recherche une nouvelle adresse pour ta marque.',
                  value: 'Ex. monentreprise.com',
                  actionLabel: 'Rechercher ci-dessous',
                  onTap: () => FocusScope.of(context).requestFocus(),
                )),
          ]);
        }),
        const SizedBox(height: 24),
        _SearchCard(
          controller: _searchController,
          searching: _searching,
          result: _searchResult,
          onSearch: _search,
          onAdd: _addSearchedDomain,
        ),
        const SizedBox(height: 24),
        _LaunchChecklist(publish: publish),
        const SizedBox(height: 20),
        SizedBox(
          height: 54,
          child: FilledButton.icon(
            onPressed: isPublishing || projectId == null ? null : _publish,
            icon: isPublishing
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.rocket_launch_outlined),
            label: Text(isPublishing
                ? 'Publication en cours…'
                : 'Publier sur ${publish.domain}'),
          ),
        ),
      ],
    );
  }

  Future<void> _showDomainPicker(
      List<ManagedDomain> domains, String? projectId) async {
    final available = domains
        .where((d) => d.isAvailableForProject || d.projectId == projectId)
        .toList();
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
          child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Choisir une adresse',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 12),
              if (available.isEmpty)
                const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child:
                        Text('Tous tes domaines sont déjà liés à un projet.')),
              ...available.map((domain) => ListTile(
                    leading: Icon(domain.isSubdomain
                        ? Icons.account_tree_outlined
                        : Icons.language),
                    title: Text(domain.name),
                    subtitle: Text(domain.isSubdomain
                        ? 'Sous-domaine'
                        : 'Domaine principal'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {
                      Navigator.pop(context);
                      _selectDomain(domain);
                    },
                  )),
            ]),
      )),
    );
  }

  Future<void> _publish() async {
    try {
      await ref.read(projectWorkspaceProvider.notifier).publishSite();
      if (mounted)
        NotificationService.success(
            context, 'Ton site est maintenant en ligne.');
    } catch (_) {
      if (mounted)
        NotificationService.error(context,
            'La publication a échoué. Vérifie la configuration puis réessaie.');
    }
  }

  Future<void> _download(String projectId) async {
    try {
      final url =
          await ref.read(publishingRepositoryProvider).downloadUrl(projectId);
      await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
    } catch (_) {
      if (mounted)
        NotificationService.error(
            context, 'Le téléchargement n’a pas pu démarrer.');
    }
  }
}

class _StatusHero extends StatelessWidget {
  const _StatusHero({required this.publish});
  final PublishState publish;

  @override
  Widget build(BuildContext context) {
    final online = publish.status == 'published';
    final url = publish.url ?? 'https://${publish.domain}';
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
          gradient: AppColors.heroGradient,
          borderRadius: BorderRadius.circular(24)),
      child: Wrap(
          alignment: WrapAlignment.spaceBetween,
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 20,
          runSpacing: 16,
          children: [
            Row(mainAxisSize: MainAxisSize.min, children: [
              Container(
                  width: 52,
                  height: 52,
                  decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: .16),
                      borderRadius: BorderRadius.circular(16)),
                  child: Icon(
                      online
                          ? Icons.check_circle_outline
                          : Icons.cloud_outlined,
                      color: Colors.white)),
              const SizedBox(width: 16),
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(
                    online
                        ? 'Ton site est en ligne'
                        : 'Prêt pour la mise en ligne',
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.w800)),
                const SizedBox(height: 3),
                Text(url, style: const TextStyle(color: Colors.white70)),
              ]),
            ]),
            if (online)
              Wrap(children: [
                IconButton(
                    tooltip: 'Copier',
                    onPressed: () =>
                        Clipboard.setData(ClipboardData(text: url)),
                    icon: const Icon(Icons.copy_outlined)),
                IconButton(
                    tooltip: 'Ouvrir',
                    onPressed: () => launchUrl(Uri.parse(url),
                        mode: LaunchMode.externalApplication),
                    icon: const Icon(Icons.open_in_new)),
              ]),
          ]),
    );
  }
}

class _DomainChoice extends StatelessWidget {
  const _DomainChoice(
      {required this.selected,
      required this.icon,
      required this.title,
      required this.description,
      required this.value,
      required this.actionLabel,
      required this.onTap,
      this.secondaryLabel,
      this.onSecondary});
  final bool selected;
  final IconData icon;
  final String title;
  final String description;
  final String value;
  final String actionLabel;
  final VoidCallback onTap;
  final String? secondaryLabel;
  final VoidCallback? onSecondary;

  @override
  Widget build(BuildContext context) => Card(
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
            side: BorderSide(
                color: selected ? AppColors.primary : AppColors.borderSoft,
                width: selected ? 2 : 1)),
        child: Padding(
            padding: const EdgeInsets.all(20),
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [
                Container(
                    width: 42,
                    height: 42,
                    decoration: BoxDecoration(
                        color: AppColors.primary.withValues(alpha: .12),
                        borderRadius: BorderRadius.circular(12)),
                    child: Icon(icon, color: AppColors.primary)),
                const Spacer(),
                if (selected)
                  const Icon(Icons.check_circle, color: AppColors.success)
              ]),
              const SizedBox(height: 18),
              Text(title,
                  style: const TextStyle(
                      fontWeight: FontWeight.w800, fontSize: 16)),
              const SizedBox(height: 6),
              Text(description,
                  style: const TextStyle(
                      color: AppColors.textSecondary, fontSize: 13)),
              const SizedBox(height: 16),
              Text(value,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w700)),
              const SizedBox(height: 14),
              SizedBox(
                  width: double.infinity,
                  child: selected
                      ? OutlinedButton(
                          onPressed: null, child: const Text('Sélectionné'))
                      : OutlinedButton(
                          onPressed: onTap, child: Text(actionLabel))),
              if (secondaryLabel != null)
                Center(
                    child: TextButton(
                        onPressed: onSecondary, child: Text(secondaryLabel!))),
            ])),
      );
}

class _SearchCard extends StatelessWidget {
  const _SearchCard(
      {required this.controller,
      required this.searching,
      required this.result,
      required this.onSearch,
      required this.onAdd});
  final TextEditingController controller;
  final bool searching;
  final DomainSearchResult? result;
  final VoidCallback onSearch;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) => Card(
      child: Padding(
          padding: const EdgeInsets.all(22),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Recherche de domaine',
                style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
            const SizedBox(height: 4),
            const Text('Saisis le domaine complet souhaité.',
                style: TextStyle(color: AppColors.textSecondary)),
            const SizedBox(height: 16),
            Row(children: [
              Expanded(
                  child: TextField(
                      controller: controller,
                      onSubmitted: (_) => onSearch(),
                      decoration: const InputDecoration(
                          prefixIcon: Icon(Icons.search),
                          hintText: 'monentreprise.com'))),
              const SizedBox(width: 10),
              FilledButton(
                  onPressed: searching ? null : onSearch,
                  child: searching
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Vérifier')),
            ]),
            if (result != null) ...[
              const SizedBox(height: 14),
              Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                      color: (result!.available
                              ? AppColors.success
                              : AppColors.danger)
                          .withValues(alpha: .1),
                      borderRadius: BorderRadius.circular(12)),
                  child: Row(children: [
                    Icon(
                        result!.available
                            ? Icons.check_circle_outline
                            : Icons.cancel_outlined,
                        color: result!.available
                            ? AppColors.success
                            : AppColors.danger),
                    const SizedBox(width: 10),
                    Expanded(
                        child: Text(
                            result!.message.isNotEmpty
                                ? result!.message
                                : result!.available
                                    ? '${result!.domain} est disponible'
                                    : '${result!.domain} est déjà enregistré',
                            style:
                                const TextStyle(fontWeight: FontWeight.w700))),
                    if (!result!.available && result!.checked)
                      FilledButton(
                          onPressed: onAdd,
                          child: const Text('Je possède ce domaine')),
                  ])),
            ],
          ])));
}

class _LaunchChecklist extends StatelessWidget {
  const _LaunchChecklist({required this.publish});
  final PublishState publish;

  @override
  Widget build(BuildContext context) => Card(
      child: Padding(
          padding: const EdgeInsets.all(22),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('2. Vérification avant publication',
                style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
            const SizedBox(height: 12),
            const _CheckRow(label: 'Contenu et design enregistrés', done: true),
            _CheckRow(
                label: 'Adresse sélectionnée : ${publish.domain}',
                done: publish.domain.isNotEmpty),
            const _CheckRow(label: 'Connexion HTTPS automatique', done: true),
            _CheckRow(
                label: 'Déploiement terminé',
                done: publish.status == 'published'),
          ])));
}

class _CheckRow extends StatelessWidget {
  const _CheckRow({required this.label, required this.done});
  final String label;
  final bool done;
  @override
  Widget build(BuildContext context) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(children: [
        Icon(done ? Icons.check_circle : Icons.radio_button_unchecked,
            size: 20,
            color: done ? AppColors.success : AppColors.textSecondary),
        const SizedBox(width: 10),
        Expanded(child: Text(label))
      ]));
}
