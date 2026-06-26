import 'package:flutter/material.dart';

import '../../../core/theme.dart';
import '../../../widgets/page_scaffold.dart';

class CommentsTab extends StatelessWidget {
  const CommentsTab({super.key});

  static const _comments = [
    {
      'author': 'Lucie Renard',
      'email': 'lucie@example.com',
      'article': 'Les tendances du web design 2026',
      'content':
          'Super article ! J\'adore particulièrement la partie sur les micro-interactions. Vous avez des recommandations d\'outils pour les implémenter facilement ?',
      'date': 'Il y a 1h',
      'status': 'pending',
    },
    {
      'author': 'Thomas Garnier',
      'email': 'thomas.g@company.fr',
      'article': 'SEO en 2026 : ce qui change vraiment',
      'content':
          'Très éclairant, merci ! Je teste les Core Web Vitals dès demain sur mon site.',
      'date': 'Il y a 3h',
      'status': 'approved',
    },
    {
      'author': 'Spammer Bot',
      'email': 'spam@spam.com',
      'article': 'Optimiser ses Core Web Vitals',
      'content': 'Buy cheap watches at our website www.spam-watches.com !!!',
      'date': 'Hier',
      'status': 'spam',
    },
    {
      'author': 'Marc Dubois',
      'email': 'marc.dubois@gmail.com',
      'article': 'Guide complet du responsive design',
      'content':
          'Excellent guide, vraiment complet. Petite question : quelle est la meilleure approche entre mobile-first et desktop-first selon vous ?',
      'date': 'Hier',
      'status': 'pending',
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
            const SectionHeader(
              title: 'Modération des commentaires',
              subtitle: '23 commentaires · 4 en attente',
            ),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _Tab(
                      label: 'En attente',
                      count: 4,
                      color: Color(0xFFF59E0B),
                      selected: true),
                  const SizedBox(width: 8),
                  _Tab(label: 'Approuvés', count: 17, color: Color(0xFF10B981)),
                  const SizedBox(width: 8),
                  _Tab(label: 'Spam', count: 2, color: Color(0xFFEF4444)),
                ],
              ),
            ),
            const SizedBox(height: 16),
            for (final c in _comments) _CommentCard(comment: c),
          ],
        ),
      ),
    );
  }
}

class _Tab extends StatelessWidget {
  const _Tab(
      {required this.label,
      required this.count,
      required this.color,
      this.selected = false});
  final String label;
  final int count;
  final Color color;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: selected ? color : AppColors.background,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: selected ? color : AppColors.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label,
              style: TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 12,
                  color: selected ? Colors.white : AppColors.textPrimary)),
          const SizedBox(width: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
            decoration: BoxDecoration(
              color: selected
                  ? Colors.white.withValues(alpha: 0.3)
                  : color.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text('$count',
                style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: selected ? Colors.white : color)),
          ),
        ],
      ),
    );
  }
}

class _CommentCard extends StatelessWidget {
  const _CommentCard({required this.comment});
  final Map<String, dynamic> comment;

  @override
  Widget build(BuildContext context) {
    final status = comment['status'] as String;
    final isPending = status == 'pending';
    final isSpam = status == 'spam';

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isSpam ? const Color(0xFFFEF2F2) : AppColors.background,
        border: Border.all(
            color: isSpam ? const Color(0xFFFECACA) : AppColors.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: AppColors.skyBlueLight,
                child: Text((comment['author'] as String).substring(0, 1),
                    style: const TextStyle(
                        color: AppColors.skyBlueDark,
                        fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(comment['author'] as String,
                        style: const TextStyle(
                            fontWeight: FontWeight.w700, fontSize: 14),
                        overflow: TextOverflow.ellipsis),
                    Text('${comment['email']}',
                        style: const TextStyle(
                            color: AppColors.textSecondary, fontSize: 12),
                        overflow: TextOverflow.ellipsis),
                    Text('sur "${comment['article']}" · ${comment['date']}',
                        style: const TextStyle(
                            color: AppColors.textSecondary, fontSize: 11),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis),
                  ],
                ),
              ),
              if (isPending)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                      color: const Color(0xFFFEF3C7),
                      borderRadius: BorderRadius.circular(20)),
                  child: const Text('En attente',
                      style: TextStyle(
                          color: Color(0xFFB45309),
                          fontSize: 11,
                          fontWeight: FontWeight.w600)),
                ),
              if (isSpam)
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                      color: const Color(0xFFFECACA),
                      borderRadius: BorderRadius.circular(20)),
                  child: const Text('Spam',
                      style: TextStyle(
                          color: Color(0xFFB91C1C),
                          fontSize: 11,
                          fontWeight: FontWeight.w600)),
                ),
            ],
          ),
          const SizedBox(height: 10),
          Text(comment['content'] as String,
              style: const TextStyle(fontSize: 13, height: 1.5)),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              if (isPending) ...[
                FilledButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.check, size: 16),
                  label: const Text('Approuver'),
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF10B981),
                    padding:
                        const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  ),
                ),
                OutlinedButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.report_gmailerrorred, size: 16),
                  label: const Text('Marquer spam'),
                  style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 8)),
                ),
              ],
              TextButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.reply, size: 16),
                  label: const Text('Répondre')),
              IconButton(
                  icon: const Icon(Icons.delete_outline,
                      size: 18, color: AppColors.danger),
                  onPressed: () {}),
            ],
          ),
        ],
      ),
    );
  }
}
