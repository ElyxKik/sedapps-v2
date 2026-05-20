import 'package:flutter/material.dart';

import '../../../core/theme.dart';
import '../../../widgets/page_scaffold.dart';

class FormsTab extends StatelessWidget {
  const FormsTab({super.key});

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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SectionHeader(
                  title: 'Formulaires',
                  subtitle: '${_forms.length} formulaires · 230 soumissions',
                  trailing: FilledButton.icon(
                    onPressed: () {},
                    icon: const Icon(Icons.add, size: 18),
                    label: const Text('Nouveau formulaire'),
                  ),
                ),
                for (final f in _forms) _FormRow(form: f),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SectionHeader(title: 'Soumissions récentes', subtitle: 'Dernières demandes reçues'),
                for (final s in _recent) _SubmissionRow(submission: s),
              ],
            ),
          ),
        ),
      ],
    );
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
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(border: Border.all(color: AppColors.border), borderRadius: BorderRadius.circular(12)),
      child: Row(
        children: [
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFF10B981), Color(0xFF34D399)]),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.dynamic_form, color: Colors.white, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(form['name'] as String, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 4),
                Wrap(
                  spacing: 12,
                  runSpacing: 4,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    Row(mainAxisSize: MainAxisSize.min, children: [
                      Icon(Icons.input, size: 12, color: AppColors.textSecondary),
                      const SizedBox(width: 4),
                      Text('${form['fields']} champs', style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                    ]),
                    Row(mainAxisSize: MainAxisSize.min, children: [
                      Icon(Icons.send, size: 12, color: AppColors.textSecondary),
                      const SizedBox(width: 4),
                      Text('${form['submissions']} soumissions', style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                    ]),
                  ],
                ),
              ],
            ),
          ),
          Switch(value: active, onChanged: (_) {}, activeThumbColor: const Color(0xFF10B981)),
          IconButton(icon: const Icon(Icons.more_horiz, size: 18), onPressed: () {}),
        ],
      ),
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
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          CircleAvatar(
            radius: 18,
            backgroundColor: AppColors.skyBlueLight,
            child: Text(initial, style: const TextStyle(color: AppColors.skyBlueDark, fontWeight: FontWeight.w700)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(submission['name'] as String, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                Text(submission['email'] as String, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(color: AppColors.skyBlueLight, borderRadius: BorderRadius.circular(20)),
            child: Text(submission['form'] as String, style: const TextStyle(color: AppColors.skyBlueDark, fontSize: 11, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}
