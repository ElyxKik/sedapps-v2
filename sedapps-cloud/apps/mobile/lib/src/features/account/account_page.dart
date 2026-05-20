import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../../widgets/animations.dart';
import '../../widgets/dialogs.dart';
import '../../widgets/notifications.dart';
import '../../widgets/page_scaffold.dart';

class AccountPage extends ConsumerWidget {
  const AccountPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return PageScaffold(
      title: 'Mon compte',
      subtitle: 'Gère ton profil, ta facturation et tes préférences',
      children: [
        FutureBuilder<Map<String, dynamic>>(
          future: ref.read(apiClientProvider).account(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Card(child: Padding(padding: EdgeInsets.all(40), child: Center(child: CircularProgressIndicator())));
            }
            if (snapshot.hasError) {
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text('Impossible de charger le compte : ${snapshot.error}', style: const TextStyle(color: AppColors.danger)),
                ),
              );
            }
            final account = snapshot.data ?? {};
            final fullName = account['full_name']?.toString();
            final email = account['email']?.toString() ?? '';
            final orgName = account['org_name']?.toString() ?? 'Organisation';
            final displayName = fullName == null || fullName.isEmpty ? email : fullName;
            return FadeInUp(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(28),
                  child: Row(
                    children: [
                      Container(
                        width: 80, height: 80,
                        decoration: BoxDecoration(
                          gradient: AppColors.heroGradient,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: const Icon(Icons.person, color: Colors.white, size: 40),
                      ),
                      const SizedBox(width: 24),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(displayName, style: Theme.of(context).textTheme.headlineSmall),
                            const SizedBox(height: 2),
                            Text(email, style: const TextStyle(color: AppColors.textSecondary)),
                            const SizedBox(height: 12),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                gradient: AppColors.heroGradient,
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.business, color: Colors.white, size: 16),
                                  const SizedBox(width: 6),
                                  Text(orgName, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13)),
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
          delay: const Duration(milliseconds: 100),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SectionHeader(title: 'Paramètres'),
                  _SettingItem(
                    icon: Icons.business_outlined,
                    color: AppColors.skyBlue,
                    label: 'Organisation',
                    value: 'Synchronisée avec le backend',
                    onTap: () => NotificationService.info(context, 'Modification de l’organisation bientôt disponible'),
                  ),
                  _SettingItem(
                    icon: Icons.credit_card,
                    color: const Color(0xFF10B981),
                    label: 'Facturation',
                    value: 'Provider externe à connecter',
                    onTap: () => NotificationService.info(context, 'Redirection vers la facturation...'),
                  ),
                  _SettingItem(
                    icon: Icons.language,
                    color: const Color(0xFFF59E0B),
                    label: 'Domaines',
                    value: '2 domaines actifs',
                    onTap: () => NotificationService.info(context, 'Gestion des domaines'),
                  ),
                  _SettingItem(
                    icon: Icons.notifications_outlined,
                    color: const Color(0xFF6366F1),
                    label: 'Notifications',
                    value: 'Email actif',
                    onTap: () => NotificationService.info(context, 'Préférences de notifications'),
                  ),
                  _SettingItem(
                    icon: Icons.security,
                    color: const Color(0xFFEC4899),
                    label: 'Sécurité',
                    value: 'Mot de passe, 2FA',
                    onTap: () => NotificationService.info(context, 'Paramètres de sécurité'),
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
                  _PreferenceItem(label: 'Langue', value: 'Français', onTap: () => NotificationService.info(context, 'Changement de langue')),
                  _PreferenceItem(label: 'Thème', value: 'Clair', onTap: () => NotificationService.info(context, 'Changement de thème')),
                  _PreferenceItem(label: 'Fuseau horaire', value: 'Europe/Paris', onTap: () => NotificationService.info(context, 'Changement de fuseau horaire')),
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
              contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              leading: Container(
                width: 40, height: 40,
                decoration: BoxDecoration(color: AppColors.danger.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
                child: const Icon(Icons.logout, color: AppColors.danger, size: 20),
              ),
              title: const Text('Se déconnecter', style: TextStyle(color: AppColors.danger, fontWeight: FontWeight.w600)),
              trailing: const Icon(Icons.chevron_right, color: AppColors.textSecondary),
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
              width: 40, height: 40,
              decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                  Text(value, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
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
  const _PreferenceItem({required this.label, required this.value, required this.onTap});
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
              child: Text(label, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(20)),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(value, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                  const SizedBox(width: 6),
                  const Icon(Icons.chevron_right, size: 16, color: AppColors.textSecondary),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
