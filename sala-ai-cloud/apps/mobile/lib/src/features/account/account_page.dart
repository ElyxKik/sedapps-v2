import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../../data/localization_provider.dart';
import '../../data/theme_provider.dart';
import '../../widgets/animations.dart';
import '../../widgets/dialogs.dart';
import '../../widgets/notifications.dart';
import '../../widgets/page_scaffold.dart';

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
  ConsumerState<_AccountPageContent> createState() =>
      _AccountPageState();
}

class _AccountPageState extends ConsumerState<_AccountPageContent> {
  static const _languageKey = 'account_language';
  static const _themeKey = 'account_theme';
  static const _timezoneKey = 'account_timezone';
  static const _emailNotificationsKey = 'account_email_notifications';

  String _language = 'Français';
  String _theme = 'Clair';
  String _timezone = 'Europe/Paris';
  bool _emailNotifications = true;

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      _language = prefs.getString(_languageKey) ?? _language;
      _theme = prefs.getString(_themeKey) ?? _theme;
      _timezone = prefs.getString(_timezoneKey) ?? _timezone;
      _emailNotifications =
          prefs.getBool(_emailNotificationsKey) ?? _emailNotifications;
    });
  }

  @override
  Widget build(BuildContext context) {
    final ref = widget.ref;
    final locale = ref.watch(localizationProvider);
    return PageScaffold(
      title: 'Mon compte',
      subtitle: 'Gère ton profil, ton abonnement et tes préférences',
      children: [
        FutureBuilder<Map<String, dynamic>>(
          future: ref.read(apiClientProvider).account(),
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
        FadeInUp(
          delay: const Duration(milliseconds: 50),
          child: FutureBuilder<Map<String, dynamic>>(
            future: ref.read(apiClientProvider).creditWallet(),
            builder: (context, snapshot) {
              final wallet = snapshot.data ?? {};
              final available = wallet['available_credits'] ?? '—';
              final balance = wallet['balance_credits'] ?? '—';
              final used = wallet['used_this_month_credits'] ?? 0;
              final quota = wallet['monthly_quota_credits'] ?? 0;
              final plan = wallet['plan']?.toString() ?? 'free';
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
                              color: const Color(0xFF0EA5E9).withValues(alpha: 0.12),
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
                                Text('Ils sont utilisés lorsque Sala AI crée ou améliore un site pour toi.',
                                    style: const TextStyle(
                                        color: AppColors.textSecondary,
                                        fontSize: 12)),
                              ],
                            ),
                          ),
                          Text('$available crédits',
                              style: const TextStyle(
                                  fontWeight: FontWeight.w800,
                                  fontSize: 18,
                                  color: Color(0xFF0EA5E9))),
                        ],
                      ),
                      const SizedBox(height: 16),
                      LinearProgressIndicator(
                        value: quota == 0
                            ? 0
                            : ((used as num).toDouble() /
                                    (quota as num).toDouble())
                                .clamp(0, 1),
                        minHeight: 8,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      const SizedBox(height: 8),
                      Text('Solde total : $balance crédits · Utilisés ce mois-ci : $used / $quota',
                          style: const TextStyle(
                              color: AppColors.textSecondary, fontSize: 12)),
                      const SizedBox(height: 6),
                      const Text('Une création de site standard utilise environ 250 crédits.',
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
                    value: _emailNotifications ? 'Email actif' : 'Email désactivé',
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
                      value: _language,
                      onTap: () => _showChoiceDialog(
                            title: 'Langue',
                            currentValue: _language,
                            values: const ['Français', 'English'],
                            onSelected: (value) {
                              ref
                                  .read(localizationProvider.notifier)
                                  .setLanguage(value);
                              setState(() => _language = value);
                            },
                          )),
                  _PreferenceItem(
                      label: 'Thème',
                      value: _theme,
                      onTap: () => _showChoiceDialog(
                            title: 'Thème',
                            currentValue: _theme,
                            values: const ['Clair', 'Sombre', 'Système'],
                            onSelected: (value) {
                              ref
                                  .read(themeProvider.notifier)
                                  .setTheme(value);
                              setState(() => _theme = value);
                            },
                          )),
                  _PreferenceItem(
                      label: 'Fuseau horaire',
                      value: _timezone,
                      onTap: () => _showChoiceDialog(
                            title: 'Fuseau horaire',
                            currentValue: _timezone,
                            values: const [
                              'Europe/Paris',
                              'Africa/Lagos',
                              'UTC'
                            ],
                            onSelected: (value) => _saveStringPreference(
                                _timezoneKey, value,
                                onSaved: () =>
                                    setState(() => _timezone = value)),
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
                  await ref.read(tokenStoreProvider).clear();
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
    required ValueChanged<String> onSelected,
  }) async {
    final selected = await showDialog<String>(
      context: context,
      builder: (context) => SimpleDialog(
        title: Text(title),
        children: [
          for (final value in values)
            RadioListTile<String>(
              value: value,
              groupValue: currentValue,
              title: Text(value),
              onChanged: (value) => Navigator.of(context).pop(value),
            ),
        ],
      ),
    );
    if (selected == null) return;
    onSelected(selected);
    if (mounted) {
      NotificationService.success(context, '$title mis à jour');
    }
  }

  Future<void> _saveStringPreference(String key, String value,
      {required VoidCallback onSaved}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(key, value);
    if (mounted) onSaved();
  }

  Future<void> _showNotificationsDialog() async {
    final enabled = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Notifications'),
        content: SwitchListTile(
          contentPadding: EdgeInsets.zero,
          title: const Text('Notifications email'),
          value: _emailNotifications,
          onChanged: (value) => Navigator.of(context).pop(value),
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
    final account = await ref.read(apiClientProvider).account();
    if (!mounted) return;
    final orgName = account['org_name']?.toString() ?? 'Organisation';
    final email = account['email']?.toString() ?? '';
    return showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Facturation'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Organisation : $orgName'),
            const SizedBox(height: 8),
            Text('Email : $email'),
            const SizedBox(height: 16),
            const Text(
                'La gestion des factures et moyens de paiement sera disponible ici dès que le module de paiement backend sera activé.'),
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

  Future<void> _showSecurityDialog() async {
    return showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Sécurité'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.verified_user_outlined),
              title: const Text('Session authentifiée'),
              subtitle: const Text('Ton accès est protégé par token sécurisé.'),
            ),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.logout, color: AppColors.danger),
              title: const Text('Déconnecter cet appareil'),
              onTap: () async {
                Navigator.of(context).pop();
                await ref.read(tokenStoreProvider).clear();
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
        builder: (context, setState) => AlertDialog(
          title: const Text('Modifier le profil'),
          content: Column(
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
                      setState(() => isSaving = true);
                      try {
                        await ref.read(apiClientProvider).updateAccount({
                          'full_name': fullNameCtrl.text.trim(),
                          'org_name': orgNameCtrl.text.trim(),
                        });
                        if (mounted) {
                          Navigator.of(context).pop();
                          NotificationService.success(
                              context, 'Profil mis à jour');
                        }
                      } catch (e) {
                        if (mounted) {
                          NotificationService.error(context,
                              'Erreur lors de la mise à jour du profil');
                        }
                      } finally {
                        if (mounted) setState(() => isSaving = false);
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
