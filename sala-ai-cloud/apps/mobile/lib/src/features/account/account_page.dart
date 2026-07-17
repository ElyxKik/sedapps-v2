import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../auth/auth_session.dart';
import 'data/billing_repository.dart';
import 'domain/credit_wallet.dart';
import '../../data/localization_provider.dart';
import '../../data/theme_provider.dart';
import '../../widgets/animations.dart';
import '../../widgets/dialogs.dart';
import '../../widgets/notifications.dart';
import '../../widgets/page_scaffold.dart';
import 'domains_section.dart';
import 'subscription_dialog.dart';

class AccountPage extends ConsumerWidget {
  const AccountPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _AccountPageContent(ref: ref);
  }
}

class _AccountPageContent extends ConsumerStatefulWidget {
  final WidgetRef ref;

  const _AccountPageContent({required this.ref});

  @override
  ConsumerState<_AccountPageContent> createState() => _AccountPageState();
}

class _AccountPageState extends ConsumerState<_AccountPageContent> {
  static const _emailNotificationsKey = 'account_email_notifications';

  bool _emailNotifications = true;
  late Future<Map<String, dynamic>> _accountFuture;

  @override
  void initState() {
    super.initState();
    _accountFuture = widget.ref.read(apiClientProvider).account();
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      _emailNotifications =
          prefs.getBool(_emailNotificationsKey) ?? _emailNotifications;
    });
  }

  @override
  Widget build(BuildContext context) {
    final ref = widget.ref;
    final language = ref.watch(localizationProvider);
    final themeMode = ref.watch(themeProvider);
    final themeName = switch (themeMode) {
      ThemeMode.dark => 'Sombre',
      ThemeMode.system => 'Système',
      _ => 'Clair',
    };
    return PageScaffold(
      title: 'Mon compte',
      subtitle: 'Gère ton profil, ton abonnement et tes préférences',
      children: [
        FutureBuilder<Map<String, dynamic>>(
          future: _accountFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Card(
                  child: Padding(
                      padding: EdgeInsets.all(40),
                      child: Center(child: CircularProgressIndicator())));
            }
            if (snapshot.hasError) {
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(
                      'Impossible de charger ton compte. Vérifie ta connexion et réessaie.',
                      style: const TextStyle(color: AppColors.danger)),
                ),
              );
            }
            final account = snapshot.data ?? {};
            final fullName = account['full_name']?.toString();
            final email = account['email']?.toString() ?? '';
            final orgName = account['org_name']?.toString() ?? 'Organisation';
            final displayName =
                fullName == null || fullName.isEmpty ? email : fullName;
            return FadeInUp(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(28),
                  child: Row(
                    children: [
                      Container(
                        width: 80,
                        height: 80,
                        decoration: BoxDecoration(
                          gradient: AppColors.heroGradient,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: const Icon(Icons.person,
                            color: Colors.white, size: 40),
                      ),
                      const SizedBox(width: 24),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(displayName,
                                style:
                                    Theme.of(context).textTheme.headlineSmall),
                            const SizedBox(height: 2),
                            Text(email,
                                style: const TextStyle(
                                    color: AppColors.textSecondary)),
                            const SizedBox(height: 12),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                gradient: AppColors.heroGradient,
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.business,
                                      color: Colors.white, size: 16),
                                  const SizedBox(width: 6),
                                  Text(orgName,
                                      style: const TextStyle(
                                          color: Colors.white,
                                          fontWeight: FontWeight.w700,
                                          fontSize: 13)),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
        const SizedBox(height: 24),
        const FadeInUp(
          delay: Duration(milliseconds: 75),
          child: AccountDomainsSection(),
        ),
        const SizedBox(height: 24),
        FadeInUp(
          delay: const Duration(milliseconds: 50),
          child: FutureBuilder<CreditWallet>(
            future: ref.read(billingRepositoryProvider).wallet(),
            builder: (context, snapshot) {
              final wallet = snapshot.data;
              final available = wallet?.available;
              final balance = wallet?.balance;
              final used = wallet?.usedThisMonth ?? 0;
              final quota = wallet?.monthlyQuota ?? 0;
              final plan = wallet?.plan ?? 'free';
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 44,
                            height: 44,
                            decoration: BoxDecoration(
                              color: const Color(0xFF0EA5E9)
                                  .withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(Icons.auto_awesome,
                                color: Color(0xFF0EA5E9)),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Crédits de création',
                                    style: TextStyle(
                                        fontWeight: FontWeight.w800,
                                        fontSize: 16)),
                                Text(
                                    'Ils sont utilisés lorsque Sala AI crée ou améliore un site pour toi.',
                                    style: const TextStyle(
                                        color: AppColors.textSecondary,
                                        fontSize: 12)),
                              ],
                            ),
                          ),
                          Text('${available ?? '—'} crédits',
                              style: const TextStyle(
                                  fontWeight: FontWeight.w800,
                                  fontSize: 18,
                                  color: Color(0xFF0EA5E9))),
                        ],
                      ),
                      const SizedBox(height: 16),
                      LinearProgressIndicator(
                        value: wallet?.usageRatio ?? 0,
                        minHeight: 8,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      const SizedBox(height: 8),
                      Text(
                          'Solde total : ${balance ?? '—'} crédits · Utilisés ce mois-ci : $used / $quota · Plan $plan',
                          style: const TextStyle(
                              color: AppColors.textSecondary, fontSize: 12)),
                      const SizedBox(height: 6),
                      const Text(
                          '1 crédit = 1 000 tokens IA. Une création standard réserve 250 crédits, puis seul l’usage réel est débité.',
                          style: TextStyle(
                              color: AppColors.textSecondary, fontSize: 12)),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 24),
        FadeInUp(
          delay: const Duration(milliseconds: 100),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SectionHeader(title: 'Mon espace'),
                  _SettingItem(
                    icon: Icons.edit_outlined,
                    color: const Color(0xFF0369A1),
                    label: 'Informations personnelles',
                    value: 'Nom et entreprise',
                    onTap: () => _showEditProfileDialog(ref),
                  ),
                  _SettingItem(
                    icon: Icons.credit_card,
                    color: const Color(0xFF10B981),
                    label: 'Abonnement et paiement',
                    value: 'Gérer mon abonnement',
                    onTap: _showBillingDialog,
                  ),
                  _SettingItem(
                    icon: Icons.language,
                    color: const Color(0xFFF59E0B),
                    label: 'Adresses de mes sites',
                    value: 'Voir mes sites',
                    onTap: () => context.go('/projects'),
                  ),
                  _SettingItem(
                    icon: Icons.notifications_outlined,
                    color: const Color(0xFF0EA5E9),
                    label: 'Notifications',
                    value:
                        _emailNotifications ? 'Email actif' : 'Email désactivé',
                    onTap: _showNotificationsDialog,
                  ),
                  _SettingItem(
                    icon: Icons.security,
                    color: const Color(0xFF0EA5E9),
                    label: 'Connexion et sécurité',
                    value: 'Compte connecté',
                    onTap: _showSecurityDialog,
                  ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 20),
        FadeInUp(
          delay: const Duration(milliseconds: 200),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SectionHeader(title: 'Préférences'),
                  _PreferenceItem(
                      label: 'Langue',
                      value: language,
                      onTap: () => _showChoiceDialog(
                            title: 'Langue',
                            currentValue: language,
                            values: const ['Français', 'English'],
                            onSelected: (value) => ref
                                .read(localizationProvider.notifier)
                                .setLanguage(value),
                          )),
                  _PreferenceItem(
                      label: 'Thème',
                      value: themeName,
                      onTap: () => _showChoiceDialog(
                            title: 'Thème',
                            currentValue: themeName,
                            values: const ['Clair', 'Sombre', 'Système'],
                            onSelected: (value) => ref
                                .read(themeProvider.notifier)
                                .setTheme(value),
                          )),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 20),
        FadeInUp(
          delay: const Duration(milliseconds: 300),
          child: Card(
            child: ListTile(
              contentPadding:
                  const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                    color: AppColors.danger.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(10)),
                child:
                    const Icon(Icons.logout, color: AppColors.danger, size: 20),
              ),
              title: const Text('Se déconnecter',
                  style: TextStyle(
                      color: AppColors.danger, fontWeight: FontWeight.w600)),
              trailing: const Icon(Icons.chevron_right,
                  color: AppColors.textSecondary),
              onTap: () => showConfirmDialog(
                context,
                title: 'Se déconnecter',
                message: 'Es-tu sûr de vouloir te déconnecter ?',
                confirmText: 'Déconnecter',
                onConfirm: () async {
                  await ref.read(authSessionProvider.notifier).logout();
                  if (context.mounted) context.go('/login');
                },
              ),
            ),
          ),
        ),
      ],
    );
  }

  Future<void> _showChoiceDialog({
    required String title,
    required String currentValue,
    required List<String> values,
    required Future<void> Function(String) onSelected,
  }) async {
    final selected = await showDialog<String>(
      context: context,
      builder: (context) => _AccountDialog(
        icon: title == 'Langue' ? Icons.translate : Icons.palette_outlined,
        title: title,
        subtitle: 'Le changement est appliqué immédiatement et mémorisé.',
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          for (final value in values)
            Container(
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(
                color: value == currentValue
                    ? AppColors.primary.withValues(alpha: .12)
                    : AppColors.surfaceMuted,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                    color: value == currentValue
                        ? AppColors.primary
                        : AppColors.borderSoft),
              ),
              child: RadioListTile<String>(
                value: value,
                groupValue: currentValue,
                title: Text(value,
                    style: const TextStyle(fontWeight: FontWeight.w700)),
                onChanged: (value) => Navigator.of(context).pop(value),
              ),
            ),
        ]),
      ),
    );
    if (selected == null) return;
    await onSelected(selected);
    if (mounted) {
      NotificationService.success(context, '$title mis à jour');
    }
  }

  Future<void> _showNotificationsDialog() async {
    final enabled = await showDialog<bool>(
      context: context,
      builder: (context) => _AccountDialog(
        icon: Icons.notifications_outlined,
        title: 'Notifications',
        subtitle: 'Choisis comment SalaAI peut te tenir informé.',
        child: Container(
          decoration: BoxDecoration(
              color: AppColors.surfaceMuted,
              borderRadius: BorderRadius.circular(14)),
          child: SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Notifications email'),
            subtitle:
                const Text('Publications, domaines et alertes importantes'),
            value: _emailNotifications,
            onChanged: (value) => Navigator.of(context).pop(value),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Fermer'),
          ),
        ],
      ),
    );
    if (enabled == null) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_emailNotificationsKey, enabled);
    setState(() => _emailNotifications = enabled);
    if (mounted) {
      NotificationService.success(context, 'Notifications mises à jour');
    }
  }

  Future<void> _showBillingDialog() async {
    if (!mounted) return;
    return showSubscriptionDialog(
      context: context,
      repository: ref.read(billingRepositoryProvider),
    );
  }

  Future<void> _showSecurityDialog() async {
    return showDialog<void>(
      context: context,
      builder: (context) => _AccountDialog(
        icon: Icons.shield_outlined,
        title: 'Connexion et sécurité',
        subtitle: 'Contrôle la session actuellement ouverte.',
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
                decoration: BoxDecoration(
                    color: AppColors.success.withValues(alpha: .08),
                    borderRadius: BorderRadius.circular(14)),
                child: const ListTile(
                  leading: const Icon(Icons.verified_user_outlined),
                  title: const Text('Session authentifiée'),
                  subtitle:
                      const Text('Ton accès est protégé par token sécurisé.'),
                )),
            const SizedBox(height: 10),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.logout, color: AppColors.danger),
              title: const Text('Déconnecter cet appareil'),
              onTap: () async {
                Navigator.of(context).pop();
                await ref.read(authSessionProvider.notifier).logout();
                if (mounted) context.go('/login');
              },
            ),
          ],
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Fermer')),
        ],
      ),
    );
  }

  Future<void> _showEditProfileDialog(WidgetRef ref) async {
    final account = await ref.read(apiClientProvider).account();
    if (!mounted) return;

    final fullNameCtrl =
        TextEditingController(text: account['full_name']?.toString() ?? '');
    final orgNameCtrl =
        TextEditingController(text: account['org_name']?.toString() ?? '');
    bool isSaving = false;

    return showDialog<void>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => _AccountDialog(
          icon: Icons.person_outline,
          title: 'Informations personnelles',
          subtitle: 'Mets à jour les informations visibles dans ton espace.',
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: fullNameCtrl,
                decoration: const InputDecoration(
                  labelText: 'Nom complet',
                  prefixIcon: Icon(Icons.person_outline),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: orgNameCtrl,
                decoration: const InputDecoration(
                  labelText: 'Organisation',
                  prefixIcon: Icon(Icons.business_outlined),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: isSaving ? null : () => Navigator.of(context).pop(),
              child: const Text('Annuler'),
            ),
            FilledButton(
              onPressed: isSaving
                  ? null
                  : () async {
                      setDialogState(() => isSaving = true);
                      try {
                        await ref.read(apiClientProvider).updateAccount({
                          'full_name': fullNameCtrl.text.trim(),
                          'org_name': orgNameCtrl.text.trim(),
                        });
                        _accountFuture = ref.read(apiClientProvider).account();
                        if (mounted) {
                          Navigator.of(context).pop();
                          this.setState(() {});
                          NotificationService.success(
                              context, 'Profil mis à jour');
                        }
                      } catch (e) {
                        if (mounted) {
                          NotificationService.error(context,
                              'Erreur lors de la mise à jour du profil');
                        }
                      } finally {
                        if (mounted) setDialogState(() => isSaving = false);
                      }
                    },
              child: isSaving
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Enregistrer'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showInfoDialog({
    required String title,
    required String message,
  }) {
    return showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }
}

class _SettingItem extends StatelessWidget {
  const _SettingItem({
    required this.icon,
    required this.color,
    required this.label,
    required this.value,
    required this.onTap,
  });
  final IconData icon;
  final Color color;
  final String label;
  final String value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(10)),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label,
                      style: const TextStyle(
                          fontWeight: FontWeight.w600, fontSize: 14)),
                  Text(value,
                      style: const TextStyle(
                          color: AppColors.textSecondary, fontSize: 12)),
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

class _PreferenceItem extends StatelessWidget {
  const _PreferenceItem(
      {required this.label, required this.value, required this.onTap});
  final String label;
  final String value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
        child: Row(
          children: [
            Expanded(
              child: Text(label,
                  style: const TextStyle(
                      fontWeight: FontWeight.w600, fontSize: 14)),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                  color: AppColors.background,
                  borderRadius: BorderRadius.circular(20)),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(value,
                      style: const TextStyle(
                          color: AppColors.textSecondary, fontSize: 13)),
                  const SizedBox(width: 6),
                  const Icon(Icons.chevron_right,
                      size: 16, color: AppColors.textSecondary),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AccountDialog extends StatelessWidget {
  const _AccountDialog({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.child,
    this.actions = const [],
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final Widget child;
  final List<Widget> actions;

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 520),
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: AppColors.border),
            boxShadow: const [
              BoxShadow(
                  color: Colors.black54, blurRadius: 40, offset: Offset(0, 18)),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                Container(
                  width: 46,
                  height: 46,
                  decoration: BoxDecoration(
                    gradient: AppColors.heroGradient,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Icon(icon, color: Colors.white),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title,
                          style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 2),
                      Text(subtitle,
                          style: const TextStyle(
                              color: AppColors.textSecondary, fontSize: 12)),
                    ],
                  ),
                ),
                IconButton(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close)),
              ]),
              const SizedBox(height: 22),
              Flexible(child: SingleChildScrollView(child: child)),
              if (actions.isNotEmpty) ...[
                const SizedBox(height: 20),
                Row(mainAxisAlignment: MainAxisAlignment.end, children: [
                  for (var i = 0; i < actions.length; i++) ...[
                    if (i > 0) const SizedBox(width: 10),
                    actions[i],
                  ],
                ]),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoTile extends StatelessWidget {
  const _InfoTile(
      {required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
            color: AppColors.surfaceMuted,
            borderRadius: BorderRadius.circular(14)),
        child: Row(children: [
          Icon(icon, color: AppColors.primary),
          const SizedBox(width: 12),
          Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                Text(label,
                    style: const TextStyle(
                        color: AppColors.textSecondary, fontSize: 11)),
                Text(value,
                    style: const TextStyle(fontWeight: FontWeight.w700)),
              ])),
        ]),
      );
}
