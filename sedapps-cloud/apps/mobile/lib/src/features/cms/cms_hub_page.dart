import 'package:flutter/material.dart';

import '../../core/theme.dart';
import '../../widgets/page_scaffold.dart';
import 'tabs/blog_tab.dart';
import 'tabs/comments_tab.dart';
import 'tabs/forms_tab.dart';
import 'tabs/media_tab.dart';
import 'tabs/pages_tab.dart';

class CmsHubPage extends StatefulWidget {
  const CmsHubPage({super.key});

  @override
  State<CmsHubPage> createState() => _CmsHubPageState();
}

class _CmsHubPageState extends State<CmsHubPage> {
  int _selected = 0;

  static const _sections = [
    _CmsSection('Blog', Icons.article_outlined, Icons.article_rounded, 'Articles & catégories', AppColors.skyBlue),
    _CmsSection('Formulaires', Icons.dynamic_form_outlined, Icons.dynamic_form_rounded, 'Contact, devis, newsletter', Color(0xFF10B981)),
    _CmsSection('Commentaires', Icons.comment_outlined, Icons.comment_rounded, 'Modération', Color(0xFFF59E0B)),
    _CmsSection('Pages', Icons.web_outlined, Icons.web_rounded, 'À propos, Contact, Légal', Color(0xFF6366F1)),
    _CmsSection('Médias', Icons.image_outlined, Icons.image_rounded, 'Images, vidéos, fichiers', Color(0xFFEC4899)),
  ];

  @override
  Widget build(BuildContext context) {
    return PageScaffold(
      title: 'CMS',
      subtitle: 'Gère le contenu de tes sites : blog, formulaires, commentaires...',
      children: [
        _StatsRow(),
        const SizedBox(height: 24),
        LayoutBuilder(
          builder: (context, constraints) {
            final wide = constraints.maxWidth > 900;
            if (wide) {
              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(width: 260, child: _SideNav(sections: _sections, selected: _selected, onSelect: (i) => setState(() => _selected = i))),
                  const SizedBox(width: 20),
                  Expanded(child: _content()),
                ],
              );
            }
            return Column(
              children: [
                _TopChips(sections: _sections, selected: _selected, onSelect: (i) => setState(() => _selected = i)),
                const SizedBox(height: 16),
                _content(),
              ],
            );
          },
        ),
      ],
    );
  }

  Widget _content() {
    switch (_selected) {
      case 0:
        return const BlogTab();
      case 1:
        return const FormsTab();
      case 2:
        return const CommentsTab();
      case 3:
        return const PagesTab();
      case 4:
        return const MediaTab();
      default:
        return const SizedBox.shrink();
    }
  }
}

class _CmsSection {
  const _CmsSection(this.label, this.icon, this.selectedIcon, this.desc, this.color);
  final String label;
  final IconData icon;
  final IconData selectedIcon;
  final String desc;
  final Color color;
}

class _SideNav extends StatelessWidget {
  const _SideNav({required this.sections, required this.selected, required this.onSelect});
  final List<_CmsSection> sections;
  final int selected;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            for (var i = 0; i < sections.length; i++) ...[
              _NavItem(section: sections[i], selected: selected == i, onTap: () => onSelect(i)),
              const SizedBox(height: 4),
            ],
          ],
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem({required this.section, required this.selected, required this.onTap});
  final _CmsSection section;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: selected ? section.color.withValues(alpha: 0.1) : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Container(
              width: 36, height: 36,
              decoration: BoxDecoration(
                color: selected ? section.color : section.color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                selected ? section.selectedIcon : section.icon,
                color: selected ? Colors.white : section.color,
                size: 18,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(section.label,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: selected ? section.color : AppColors.textPrimary,
                        fontSize: 14,
                      )),
                  Text(section.desc,
                      style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TopChips extends StatelessWidget {
  const _TopChips({required this.sections, required this.selected, required this.onSelect});
  final List<_CmsSection> sections;
  final int selected;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 48,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: sections.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, i) {
          final s = sections[i];
          final isSel = selected == i;
          return GestureDetector(
            onTap: () => onSelect(i),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: isSel ? s.color : AppColors.surface,
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: isSel ? s.color : AppColors.border),
              ),
              child: Row(
                children: [
                  Icon(s.icon, size: 16, color: isSel ? Colors.white : s.color),
                  const SizedBox(width: 6),
                  Text(s.label, style: TextStyle(fontWeight: FontWeight.w600, color: isSel ? Colors.white : AppColors.textPrimary, fontSize: 13)),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}

class _StatsRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth > 900 ? 5 : constraints.maxWidth > 600 ? 3 : 2;
        return GridView.count(
          crossAxisCount: columns,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          childAspectRatio: 2.2,
          children: const [
            _MiniStat(icon: Icons.article_outlined, label: 'Articles', value: '12', color: AppColors.skyBlue),
            _MiniStat(icon: Icons.dynamic_form_outlined, label: 'Formulaires', value: '4', color: Color(0xFF10B981)),
            _MiniStat(icon: Icons.comment_outlined, label: 'Commentaires', value: '23', color: Color(0xFFF59E0B)),
            _MiniStat(icon: Icons.web_outlined, label: 'Pages', value: '8', color: Color(0xFF6366F1)),
            _MiniStat(icon: Icons.image_outlined, label: 'Médias', value: '47', color: Color(0xFFEC4899)),
          ],
        );
      },
    );
  }
}

class _MiniStat extends StatelessWidget {
  const _MiniStat({required this.icon, required this.label, required this.value, required this.color});
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Container(
              width: 36, height: 36,
              decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
              child: Icon(icon, color: color, size: 18),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                  Text(label, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
