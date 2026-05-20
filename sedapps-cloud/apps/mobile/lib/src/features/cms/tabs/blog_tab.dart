import 'package:flutter/material.dart';

import '../../../core/theme.dart';
import '../../../widgets/page_scaffold.dart';

class BlogTab extends StatelessWidget {
  const BlogTab({super.key});

  static const _articles = [
    {'title': 'Les tendances du web design 2026', 'status': 'published', 'date': '15 mars', 'views': '1.2k', 'comments': 8},
    {'title': 'Guide complet du responsive design', 'status': 'draft', 'date': '12 mars', 'views': '0', 'comments': 0},
    {'title': 'SEO en 2026 : ce qui change vraiment', 'status': 'published', 'date': '08 mars', 'views': '3.4k', 'comments': 24},
    {'title': 'Comment l\'IA transforme le no-code', 'status': 'review', 'date': '05 mars', 'views': '0', 'comments': 0},
    {'title': 'Optimiser ses Core Web Vitals', 'status': 'published', 'date': '02 mars', 'views': '892', 'comments': 5},
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
              title: 'Articles de blog',
              subtitle: '${_articles.length} articles · 12.4k vues totales',
              trailing: FilledButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.add, size: 18),
                label: const Text('Nouvel article'),
              ),
            ),
            const SizedBox(height: 8),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  _FilterChip(label: 'Tous', count: 12, selected: true),
                  const SizedBox(width: 8),
                  _FilterChip(label: 'Publiés', count: 8),
                  const SizedBox(width: 8),
                  _FilterChip(label: 'Brouillons', count: 3),
                  const SizedBox(width: 8),
                  _FilterChip(label: 'En revue', count: 1),
                ],
              ),
            ),
            const SizedBox(height: 16),
            for (final a in _articles) _ArticleRow(article: a),
          ],
        ),
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({required this.label, required this.count, this.selected = false});
  final String label;
  final int count;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: selected ? AppColors.skyBlue : AppColors.background,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: selected ? AppColors.skyBlue : AppColors.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label, style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12, color: selected ? Colors.white : AppColors.textPrimary)),
          const SizedBox(width: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
            decoration: BoxDecoration(
              color: selected ? Colors.white.withValues(alpha: 0.25) : AppColors.skyBlueLight,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text('$count', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: selected ? Colors.white : AppColors.skyBlueDark)),
          ),
        ],
      ),
    );
  }
}

class _ArticleRow extends StatelessWidget {
  const _ArticleRow({required this.article});
  final Map<String, dynamic> article;

  @override
  Widget build(BuildContext context) {
    final status = article['status'] as String;
    final colors = {
      'published': const Color(0xFF10B981),
      'draft': AppColors.textSecondary,
      'review': const Color(0xFFF59E0B),
    };
    final labels = {'published': 'Publié', 'draft': 'Brouillon', 'review': 'En revue'};
    final color = colors[status]!;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.border),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
            child: Icon(Icons.article, color: color, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(article['title'] as String, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 4),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(20)),
                        child: Text(labels[status]!, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600)),
                      ),
                      const SizedBox(width: 12),
                      Icon(Icons.calendar_today_outlined, size: 12, color: AppColors.textSecondary),
                      const SizedBox(width: 4),
                      Text(article['date'] as String, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                      const SizedBox(width: 12),
                      Icon(Icons.visibility_outlined, size: 12, color: AppColors.textSecondary),
                      const SizedBox(width: 4),
                      Text(article['views'] as String, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                      const SizedBox(width: 12),
                      Icon(Icons.comment_outlined, size: 12, color: AppColors.textSecondary),
                      const SizedBox(width: 4),
                      Text('${article['comments']}', style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          IconButton(icon: const Icon(Icons.edit_outlined, size: 18), onPressed: () {}),
          IconButton(icon: const Icon(Icons.more_horiz, size: 18), onPressed: () {}),
        ],
      ),
    );
  }
}
