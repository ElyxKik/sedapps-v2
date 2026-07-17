import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../widgets/notifications.dart';
import '../publish/data/domains_repository.dart';
import '../publish/domain/managed_domain.dart';

class AccountDomainsSection extends ConsumerWidget {
  const AccountDomainsSection({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final domains = ref.watch(managedDomainsProvider);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: .12),
                    borderRadius: BorderRadius.circular(12)),
                child: const Icon(Icons.language, color: AppColors.primary)),
            const SizedBox(width: 13),
            const Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                  Text('Mes domaines',
                      style:
                          TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
                  Text('Adresses, affectations et renouvellements',
                      style: TextStyle(
                          color: AppColors.textSecondary, fontSize: 12)),
                ])),
            FilledButton.icon(
                onPressed: () => _addDomain(context, ref),
                icon: const Icon(Icons.add, size: 18),
                label: const Text('Ajouter')),
          ]),
          const SizedBox(height: 18),
          domains.when(
            loading: () => const Center(
                child: Padding(
                    padding: EdgeInsets.all(20),
                    child: CircularProgressIndicator())),
            error: (_, __) => const Text('Impossible de charger les domaines.',
                style: TextStyle(color: AppColors.danger)),
            data: (items) => items.isEmpty
                ? Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(22),
                    decoration: BoxDecoration(
                        color: AppColors.surfaceMuted,
                        borderRadius: BorderRadius.circular(14)),
                    child: const Column(children: [
                      Icon(Icons.public_off_outlined,
                          color: AppColors.textSecondary),
                      SizedBox(height: 8),
                      Text('Aucun domaine ajouté'),
                      Text(
                          'Ajoute un domaine existant ou recherche-en un depuis Mise en ligne.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                              color: AppColors.textSecondary, fontSize: 12))
                    ]))
                : Column(
                    children: items
                        .map((domain) => _DomainRow(domain: domain))
                        .toList()),
          ),
        ]),
      ),
    );
  }

  Future<void> _addDomain(BuildContext context, WidgetRef ref) async {
    final controller = TextEditingController();
    DateTime? expiresAt;
    final accepted = await showDialog<bool>(
        context: context,
        builder: (context) => StatefulBuilder(
            builder: (context, setDialogState) => AlertDialog(
                  title: const Text('Ajouter un domaine existant'),
                  content: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                            'Ajoute un domaine que tu possèdes déjà. La vérification DNS sera demandée avant sa publication.',
                            style: TextStyle(
                                color: AppColors.textSecondary, fontSize: 13)),
                        const SizedBox(height: 16),
                        TextField(
                            controller: controller,
                            autofocus: true,
                            decoration: const InputDecoration(
                                labelText: 'Nom de domaine',
                                hintText: 'monentreprise.com')),
                        const SizedBox(height: 12),
                        OutlinedButton.icon(
                          onPressed: () async {
                            final selected = await showDatePicker(
                              context: context,
                              firstDate: DateTime.now(),
                              lastDate: DateTime.now()
                                  .add(const Duration(days: 3650)),
                              initialDate: expiresAt ??
                                  DateTime.now().add(const Duration(days: 365)),
                            );
                            if (selected != null) {
                              setDialogState(() => expiresAt = selected);
                            }
                          },
                          icon: const Icon(Icons.event_outlined),
                          label: Text(expiresAt == null
                              ? 'Renseigner la date d’expiration'
                              : 'Expiration : ${expiresAt!.day.toString().padLeft(2, '0')}/${expiresAt!.month.toString().padLeft(2, '0')}/${expiresAt!.year}'),
                        ),
                      ]),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(context, false),
                        child: const Text('Annuler')),
                    FilledButton(
                        onPressed: () => Navigator.pop(context, true),
                        child: const Text('Ajouter'))
                  ],
                )));
    if (accepted != true || controller.text.trim().isEmpty) {
      controller.dispose();
      return;
    }
    try {
      await ref
          .read(domainsRepositoryProvider)
          .add(controller.text.trim(), expiresAt: expiresAt);
      ref.invalidate(managedDomainsProvider);
      if (context.mounted)
        NotificationService.success(context, 'Domaine ajouté.');
    } catch (_) {
      if (context.mounted)
        NotificationService.error(
            context, 'Ce domaine est invalide ou déjà géré.');
    } finally {
      controller.dispose();
    }
  }
}

class _DomainRow extends ConsumerWidget {
  const _DomainRow({required this.domain});
  final ManagedDomain domain;

  String _date(DateTime? date) {
    if (date == null) return 'Date non communiquée';
    final local = date.toLocal();
    return '${local.day.toString().padLeft(2, '0')}/${local.month.toString().padLeft(2, '0')}/${local.year}';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final expiring = domain.expiresAt != null &&
        domain.expiresAt!.difference(DateTime.now()).inDays <= 30;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
          color: AppColors.surfaceMuted,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.borderSoft)),
      child: Wrap(
          alignment: WrapAlignment.spaceBetween,
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 16,
          runSpacing: 12,
          children: [
            Row(mainAxisSize: MainAxisSize.min, children: [
              Icon(
                  domain.isSubdomain
                      ? Icons.account_tree_outlined
                      : Icons.language,
                  color: AppColors.primary),
              const SizedBox(width: 12),
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(domain.name,
                    style: const TextStyle(fontWeight: FontWeight.w800)),
                const SizedBox(height: 3),
                Text(
                    domain.status == 'pending'
                        ? 'Vérification DNS requise'
                        : domain.projectId == null
                            ? 'Non lié à un projet'
                            : 'Lié à un projet',
                    style: TextStyle(
                        color: domain.status == 'pending' ||
                                domain.projectId == null
                            ? AppColors.textSecondary
                            : AppColors.success,
                        fontSize: 12)),
              ]),
            ]),
            Row(mainAxisSize: MainAxisSize.min, children: [
              Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                Text(
                    domain.isSubdomain ? 'Pas de renouvellement' : 'Expiration',
                    style: const TextStyle(
                        color: AppColors.textSecondary, fontSize: 11)),
                Text(
                    domain.isSubdomain
                        ? 'Avec le domaine principal'
                        : _date(domain.expiresAt),
                    style: TextStyle(
                        fontWeight: FontWeight.w700,
                        color: expiring ? AppColors.warning : null)),
              ]),
              if (!domain.isSubdomain) ...[
                const SizedBox(width: 14),
                if (domain.status == 'pending')
                  OutlinedButton(
                    onPressed: () => _verifyDomain(context, ref, domain),
                    child: const Text('Vérifier'),
                  )
                else
                  OutlinedButton(
                      onPressed: () async {
                        try {
                          await ref
                              .read(domainsRepositoryProvider)
                              .renew(domain.id);
                          if (context.mounted)
                            NotificationService.success(context,
                                'La demande de renouvellement a été envoyée.');
                        } catch (_) {
                          if (context.mounted)
                            NotificationService.error(context,
                                'Le renouvellement n’a pas pu être demandé.');
                        }
                      },
                      child: const Text('Renouveler')),
              ],
            ]),
          ]),
    );
  }

  Future<void> _verifyDomain(
      BuildContext context, WidgetRef ref, ManagedDomain domain) async {
    final record = domain.verificationName;
    final value = domain.verificationValue;
    if (record == null || value == null) return;
    final verify = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Vérifier le domaine'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          const Text(
              'Ajoute cet enregistrement TXT chez ton fournisseur DNS, puis lance la vérification.'),
          const SizedBox(height: 16),
          SelectableText('Nom : $record',
              style: const TextStyle(fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          SelectableText('Valeur : $value',
              style: const TextStyle(fontWeight: FontWeight.w700)),
        ]),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Plus tard')),
          FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Vérifier maintenant')),
        ],
      ),
    );
    if (verify != true) return;
    try {
      await ref.read(domainsRepositoryProvider).verify(domain.id);
      ref.invalidate(managedDomainsProvider);
      if (context.mounted)
        NotificationService.success(context, 'Domaine vérifié.');
    } catch (_) {
      if (context.mounted) {
        NotificationService.error(context,
            'Le TXT est introuvable. Attends quelques minutes puis réessaie.');
      }
    }
  }
}
