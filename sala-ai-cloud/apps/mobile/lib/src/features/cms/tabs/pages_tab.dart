import 'package:flutter/material.dart';

import '../../../core/theme.dart';
import '../../../widgets/page_scaffold.dart';

class PagesTab extends StatelessWidget {
  const PagesTab({super.key});

  static const _pages = [
    {'name': 'Accueil', 'slug': '/', 'icon': Icons.home_outlined, 'main': true},
    {
      'name': 'À propos',
      'slug': '/a-propos',
      'icon': Icons.info_outline,
      'main': false
    },
    {
      'name': 'Services',
      'slug': '/services',
      'icon': Icons.work_outline,
      'main': false
    },
    {
      'name': 'Tarifs',
      'slug': '/tarifs',
      'icon': Icons.attach_money,
      'main': false
    },
    {
      'name': 'Contact',
      'slug': '/contact',
      'icon': Icons.mail_outline,
      'main': false
    },
    {
      'name': 'Mentions légales',
      'slug': '/mentions-legales',
      'icon': Icons.gavel,
      'main': false
    },
    {'name': 'CGV', 'slug': '/cgv', 'icon': Icons.description, 'main': false},
    {
      'name': 'Politique de confidentialité',
      'slug': '/confidentialite',
      'icon': Icons.privacy_tip_outlined,
      'main': false
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SectionHeader(
              title: 'Pages du site',
              subtitle: '${_pages.length} pages publiées',
              trailing: FilledButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.add, size: 18),
                label: const Text('Nouvelle page'),
              ),
            ),
            for (final p in _pages)
              Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                    border: Border.all(color: AppColors.border),
                    borderRadius: BorderRadius.circular(12)),
                child: Row(
                  children: [
                    Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                          color: AppColors.skyBlueLight,
                          borderRadius: BorderRadius.circular(10)),
                      child: Icon(p['icon'] as IconData,
                          color: AppColors.skyBlue, size: 20),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text(p['name'] as String,
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w600,
                                      fontSize: 14)),
                              if (p['main'] == true) ...[
                                const SizedBox(width: 8),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                      color: AppColors.skyBlueLight,
                                      borderRadius: BorderRadius.circular(6)),
                                  child: const Text('Principale',
                                      style: TextStyle(
                                          fontSize: 10,
                                          color: AppColors.skyBlueDark,
                                          fontWeight: FontWeight.w700)),
                                ),
                              ],
                            ],
                          ),
                          Text(p['slug'] as String,
                              style: const TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 12)),
                        ],
                      ),
                    ),
                    IconButton(
                        icon: const Icon(Icons.open_in_new, size: 18),
                        onPressed: () {}),
                    IconButton(
                        icon: const Icon(Icons.edit_outlined, size: 18),
                        onPressed: () {}),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
