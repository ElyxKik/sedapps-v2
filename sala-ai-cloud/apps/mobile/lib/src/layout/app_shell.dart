import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/breakpoints.dart';
import '../core/theme.dart';
import '../features/agents/agent_state.dart';

class AppShell extends ConsumerStatefulWidget {
  const AppShell({required this.child, super.key});

  final Widget child;

  @override
  ConsumerState<AppShell> createState() => _AppShellState();
}

class _NavItem {
  const _NavItem(this.label, this.icon, this.selectedIcon, this.path);
  final String label;
  final IconData icon;
  final IconData selectedIcon;
  final String path;
}

const _items = <_NavItem>[
  _NavItem('Accueil', Icons.space_dashboard_outlined,
      Icons.space_dashboard_rounded, '/'),
  _NavItem('Mes sites', Icons.folder_outlined, Icons.folder_rounded, '/projects'),
  _NavItem('Créer un site', Icons.add_circle_outline, Icons.add_circle_rounded,
      '/new-site'),
  _NavItem('Mon compte', Icons.person_outline, Icons.person_rounded, '/account'),
];

class _AppShellState extends ConsumerState<AppShell> {
  bool _expanded = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) return;
      final prefs = await SharedPreferences.getInstance();
      final jobId = prefs.getString('active_generation_job_id');
      final projectId = prefs.getString('active_generation_project_id');
      if (jobId != null && jobId.isNotEmpty && mounted) {
        ref.read(currentJobIdProvider.notifier).state = jobId;
      }
      if (projectId != null && projectId.isNotEmpty && mounted) {
        ref.read(currentJobProjectIdProvider.notifier).state = projectId;
      }
    });
  }

  int _selectedIndex(String loc) {
    for (var i = _items.length - 1; i >= 0; i--) {
      if (loc == _items[i].path || loc.startsWith('${_items[i].path}/'))
        return i;
    }
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<String?>(currentJobIdProvider, (previous, next) async {
      final prefs = await SharedPreferences.getInstance();
      if (next == null || next.isEmpty) {
        await prefs.remove('active_generation_job_id');
      } else {
        await prefs.setString('active_generation_job_id', next);
      }
    });

    ref.listen<String?>(currentJobProjectIdProvider, (previous, next) async {
      final prefs = await SharedPreferences.getInstance();
      if (next == null || next.isEmpty) {
        await prefs.remove('active_generation_project_id');
      } else {
        await prefs.setString('active_generation_project_id', next);
      }
    });

    final loc = GoRouterState.of(context).matchedLocation;
    final idx = _selectedIndex(loc);
    final isDesktop = Breakpoints.isDesktop(context);

    if (!isDesktop) {
      return Scaffold(
        backgroundColor: AppColors.background,
        appBar: _MobileAppBar(),
        body: widget.child,
        bottomNavigationBar: _MobileBottomNav(
          currentIndex: idx,
          onTap: (i) => context.go(_items[i].path),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Row(
        children: [
          _DesktopSidebar(
            expanded: _expanded,
            currentIndex: idx,
            onToggle: () => setState(() => _expanded = !_expanded),
            onSelect: (i) => context.go(_items[i].path),
          ),
          Expanded(
            child: ClipRRect(
              child: widget.child,
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------- Mobile ----------------

class _MobileAppBar extends StatelessWidget implements PreferredSizeWidget {
  @override
  Size get preferredSize => const Size.fromHeight(72);

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppColors.background,
        border: Border(bottom: BorderSide(color: AppColors.borderSoft)),
      ),
      child: SafeArea(
        bottom: false,
        child: SizedBox(
          height: 72,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Flexible(child: _Logo(compact: true)),
                Row(
                  children: [
                    _CreditButton(credits: 12, onTap: () {}),
                    const SizedBox(width: 8),
                    _IconBadge(
                      icon: Icons.notifications_none_rounded,
                      hasDot: true,
                      onTap: () {},
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _MobileBottomNav extends StatelessWidget {
  const _MobileBottomNav({required this.currentIndex, required this.onTap});

  final int currentIndex;
  final ValueChanged<int> onTap;

  @override
  Widget build(BuildContext context) {
    return NavigationBar(
      selectedIndex: currentIndex.clamp(0, _items.length - 1),
      onDestinationSelected: onTap,
      destinations: [
        for (final it in _items)
          NavigationDestination(
            icon: Icon(it.icon),
            selectedIcon: Icon(it.selectedIcon),
            label: it.label,
          ),
      ],
    );
  }
}

// ---------------- Desktop sidebar ----------------

class _DesktopSidebar extends StatelessWidget {
  const _DesktopSidebar({
    required this.expanded,
    required this.currentIndex,
    required this.onToggle,
    required this.onSelect,
  });

  final bool expanded;
  final int currentIndex;
  final VoidCallback onToggle;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    final width = expanded ? 248.0 : 80.0;
    return AnimatedContainer(
      duration: const Duration(milliseconds: 220),
      curve: Curves.easeOutCubic,
      width: width,
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(right: BorderSide(color: AppColors.borderSoft)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header (logo + toggle)
          Padding(
            padding: EdgeInsets.fromLTRB(expanded ? 18 : 12, 20, 12, 20),
            child: Row(
              mainAxisAlignment: expanded
                  ? MainAxisAlignment.spaceBetween
                  : MainAxisAlignment.center,
              children: [
                if (expanded)
                  const Flexible(child: _Logo())
                else
                  const _LogoMark(),
                if (expanded)
                  _IconBadge(
                    icon: Icons.menu_open_rounded,
                    onTap: onToggle,
                  ),
              ],
            ),
          ),
          if (!expanded)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Center(
                child: _IconBadge(
                  icon: Icons.menu_rounded,
                  onTap: onToggle,
                ),
              ),
            ),
          const Divider(height: 1),
          const SizedBox(height: 12),
          // Items
          Expanded(
            child: ListView.builder(
              padding: EdgeInsets.symmetric(horizontal: expanded ? 12 : 8),
              itemCount: _items.length,
              itemBuilder: (context, i) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: _SidebarItem(
                    item: _items[i],
                    selected: i == currentIndex,
                    expanded: expanded,
                    onTap: () => onSelect(i),
                  ),
                );
              },
            ),
          ),
          // Footer
          const Divider(height: 1),
          Padding(
            padding: EdgeInsets.fromLTRB(
                expanded ? 14 : 8, 14, expanded ? 14 : 8, 18),
            child: expanded
                ? Row(
                    children: [
                      const _Avatar(),
                      const SizedBox(width: 10),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Mon compte',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                    fontWeight: FontWeight.w600,
                                    color: AppColors.textPrimary,
                                    fontSize: 13)),
                            Text('Pro plan',
                                style: TextStyle(
                                    fontSize: 11, color: AppColors.textMuted)),
                          ],
                        ),
                      ),
                      _IconBadge(
                        icon: Icons.notifications_none_rounded,
                        hasDot: true,
                        onTap: () {},
                      ),
                    ],
                  )
                : const Center(child: _Avatar()),
          ),
        ],
      ),
    );
  }
}

class _SidebarItem extends StatefulWidget {
  const _SidebarItem({
    required this.item,
    required this.selected,
    required this.expanded,
    required this.onTap,
  });

  final _NavItem item;
  final bool selected;
  final bool expanded;
  final VoidCallback onTap;

  @override
  State<_SidebarItem> createState() => _SidebarItemState();
}

class _SidebarItemState extends State<_SidebarItem> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final selected = widget.selected;
    final bg = selected
        ? AppColors.primary.withValues(alpha: 0.16)
        : _hover
            ? const Color(0x14FFFFFF)
            : Colors.transparent;
    final fg = selected ? AppColors.primaryLight : AppColors.textSecondary;

    final content = AnimatedContainer(
      duration: const Duration(milliseconds: 160),
      padding: EdgeInsets.symmetric(
          horizontal: widget.expanded ? 12 : 0, vertical: 10),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: widget.expanded
            ? MainAxisAlignment.start
            : MainAxisAlignment.center,
        children: [
          if (selected && widget.expanded)
            Container(
              width: 3,
              height: 18,
              margin: const EdgeInsets.only(right: 10),
              decoration: BoxDecoration(
                color: AppColors.primaryLight,
                borderRadius: BorderRadius.circular(4),
              ),
            ),
          Icon(selected ? widget.item.selectedIcon : widget.item.icon,
              color: fg, size: 20),
          if (widget.expanded) ...[
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                widget.item.label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: fg,
                  fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                  fontSize: 14,
                ),
              ),
            ),
          ],
        ],
      ),
    );

    final tappable = MouseRegion(
      onEnter: (_) => setState(() => _hover = true),
      onExit: (_) => setState(() => _hover = false),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: widget.onTap,
          child: content,
        ),
      ),
    );

    if (widget.expanded) return tappable;
    return Tooltip(message: widget.item.label, child: tappable);
  }
}

// ---------------- Atoms ----------------

class _Logo extends StatelessWidget {
  const _Logo({this.compact = false});
  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        const _LogoMark(),
        const SizedBox(width: 10),
        Flexible(
          child: Text(
            'Sala AI',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: compact ? 17 : 18,
              fontWeight: FontWeight.w800,
              color: AppColors.textPrimary,
              letterSpacing: -0.5,
            ),
          ),
        ),
      ],
    );
  }
}

class _LogoMark extends StatelessWidget {
  const _LogoMark();

  @override
  Widget build(BuildContext context) {
    return Image.asset(
      'assets/images/logo-sala-ai.png',
      width: 34,
      height: 34,
      fit: BoxFit.contain,
    );
  }
}

class _IconBadge extends StatelessWidget {
  const _IconBadge({required this.icon, this.hasDot = false, this.onTap});
  final IconData icon;
  final bool hasDot;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(10),
      onTap: onTap,
      child: Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(
          color: const Color(0x14FFFFFF),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.borderSoft),
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            Icon(icon, color: AppColors.textSecondary, size: 18),
            if (hasDot)
              Positioned(
                top: 9,
                right: 10,
                child: Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: AppColors.danger,
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: AppColors.surface, width: 1.5),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        gradient: AppColors.heroGradient,
        borderRadius: BorderRadius.circular(10),
      ),
      alignment: Alignment.center,
      child: const Text('S',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
    );
  }
}

class _CreditButton extends StatelessWidget {
  const _CreditButton({required this.credits, this.onTap});
  final int credits;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(10),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: const Color(0x14FFFFFF),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.borderSoft),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.auto_awesome, color: AppColors.primary, size: 16),
            const SizedBox(width: 6),
            Text(
              '$credits crédit${credits > 1 ? 's' : ''}',
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
