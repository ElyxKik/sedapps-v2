import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/breakpoints.dart';
import '../core/theme.dart';
import '../features/agents/agent_state.dart';
import '../features/account/data/account_summary_provider.dart';
import '../features/account/data/billing_repository.dart';

/// Controls the desktop navigation width from full-screen project workspaces.
final sidebarExpandedProvider = StateProvider<bool>((ref) => true);

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
  _NavItem(
      'Mes sites', Icons.folder_outlined, Icons.folder_rounded, '/projects'),
  _NavItem('Créer un site', Icons.add_circle_outline, Icons.add_circle_rounded,
      '/new-site'),
  _NavItem(
      'Mon compte', Icons.person_outline, Icons.person_rounded, '/account'),
];

class _AppShellState extends ConsumerState<AppShell> {
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

    ref.listen(currentJobProvider, (previous, next) {
      final job = next.asData?.value;
      if (job != null &&
          const {'success', 'degraded', 'failed', 'error'}
              .contains(job.status)) {
        ref.invalidate(creditWalletProvider);
      }
    });

    final loc = GoRouterState.of(context).matchedLocation;
    final idx = _selectedIndex(loc);
    final isDesktop = Breakpoints.isDesktop(context);
    final expanded = ref.watch(sidebarExpandedProvider);
    final account = ref.watch(accountSummaryProvider).asData?.value;

    if (!isDesktop) {
      return Scaffold(
        backgroundColor: AppColors.background,
        appBar: _MobileAppBar(),
        body: widget.child,
        bottomNavigationBar: _MobileBottomNav(
          currentIndex: idx,
          accountName: account?.firstName ?? 'Compte',
          onTap: (i) => context.go(_items[i].path),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Row(
        children: [
          _DesktopSidebar(
            expanded: expanded,
            currentIndex: idx,
            accountName: account?.name ?? 'Mon compte',
            accountEmail: account?.email ?? 'Chargement du profil…',
            accountInitials: account?.initials ?? 'S',
            onToggle: () =>
                ref.read(sidebarExpandedProvider.notifier).state = !expanded,
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

class _MobileAppBar extends ConsumerWidget implements PreferredSizeWidget {
  @override
  Size get preferredSize => const Size.fromHeight(72);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final credits = ref.watch(creditWalletProvider).when(
          data: (wallet) => wallet.available,
          loading: () => 0,
          error: (_, __) => 0,
        );
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
                    _CreditButton(
                        credits: credits, onTap: () => context.go('/account')),
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
  const _MobileBottomNav({
    required this.currentIndex,
    required this.accountName,
    required this.onTap,
  });

  final int currentIndex;
  final String accountName;
  final ValueChanged<int> onTap;

  @override
  Widget build(BuildContext context) {
    return NavigationBar(
      selectedIndex: currentIndex.clamp(0, _items.length - 1),
      onDestinationSelected: onTap,
      destinations: [
        for (var i = 0; i < _items.length; i++)
          NavigationDestination(
            icon: Icon(_items[i].icon),
            selectedIcon: Icon(_items[i].selectedIcon),
            label: i == 3 ? accountName : _items[i].label,
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
    required this.accountName,
    required this.accountEmail,
    required this.accountInitials,
    required this.onToggle,
    required this.onSelect,
  });

  final bool expanded;
  final int currentIndex;
  final String accountName;
  final String accountEmail;
  final String accountInitials;
  final VoidCallback onToggle;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    final collapsed = !expanded;
    return AnimatedContainer(
      duration: const Duration(milliseconds: 350),
      curve: Curves.easeInOut,
      width: collapsed ? 72 : 260,
      height: double.infinity,
      decoration: const BoxDecoration(
        color: Color(0xFF0A0A0F),
        border: Border(right: BorderSide(color: AppColors.borderSoft)),
      ),
      child: Column(
        children: [
          Container(
            height: 64,
            padding: EdgeInsets.symmetric(horizontal: collapsed ? 5 : 16),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.borderSoft)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.start,
              children: [
                const _LogoMark(),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 220),
                  child: collapsed
                      ? const SizedBox.shrink(key: ValueKey('logo-collapsed'))
                      : const Padding(
                          key: ValueKey('logo-expanded'),
                          padding: EdgeInsets.only(left: 12),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Sala AI',
                                  style: TextStyle(
                                      fontSize: 15,
                                      fontWeight: FontWeight.w800)),
                              Text('AI Builder Platform',
                                  style: TextStyle(
                                      color: Color(0xCC60A5FA), fontSize: 10)),
                            ],
                          ),
                        ),
                ),
                if (!collapsed) const Spacer(),
                Tooltip(
                  message: collapsed ? 'Développer' : 'Réduire',
                  child: IconButton(
                    onPressed: onToggle,
                    iconSize: 19,
                    padding:
                        collapsed ? EdgeInsets.zero : const EdgeInsets.all(8),
                    constraints: collapsed
                        ? const BoxConstraints.tightFor(width: 28, height: 36)
                        : const BoxConstraints(),
                    color: AppColors.textMuted,
                    icon: Icon(collapsed
                        ? Icons.keyboard_double_arrow_right
                        : Icons.keyboard_double_arrow_left),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 16, 12, 8),
            child: SizedBox(
              width: double.infinity,
              height: 42,
              child: FilledButton(
                onPressed: () => onSelect(2),
                style: FilledButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: collapsed ? 0 : 14),
                  elevation: 6,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                ),
                child: Row(
                  mainAxisAlignment: collapsed
                      ? MainAxisAlignment.center
                      : MainAxisAlignment.start,
                  children: [
                    const Icon(Icons.add, size: 19),
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 220),
                      child: collapsed
                          ? const SizedBox.shrink(
                              key: ValueKey('new-collapsed'))
                          : const Padding(
                              key: ValueKey('new-expanded'),
                              padding: EdgeInsets.only(left: 10),
                              child: Text('Nouveau projet',
                                  style:
                                      TextStyle(fontWeight: FontWeight.w700))),
                    ),
                  ],
                ),
              ),
            ),
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Column(children: [
                _SidebarSection(
                  title: 'PRINCIPAL',
                  expanded: expanded,
                  children: [
                    for (final i in [0, 1])
                      _SidebarItem(
                          item: _items[i],
                          selected: i == currentIndex,
                          expanded: expanded,
                          onTap: () => onSelect(i)),
                  ],
                ),
                _SidebarSection(
                  title: 'COMPTE',
                  expanded: expanded,
                  children: [
                    _SidebarItem(
                        item: _items[3],
                        selected: currentIndex == 3,
                        expanded: expanded,
                        onTap: () => onSelect(3)),
                  ],
                ),
              ]),
            ),
          ),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: AppColors.borderSoft))),
            child: Row(
              mainAxisAlignment: collapsed
                  ? MainAxisAlignment.center
                  : MainAxisAlignment.start,
              children: [
                _Avatar(initials: accountInitials),
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 220),
                  child: collapsed
                      ? const SizedBox.shrink(
                          key: ValueKey('account-collapsed'))
                      : Padding(
                          key: ValueKey('account-expanded'),
                          padding: const EdgeInsets.only(left: 12),
                          child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                SizedBox(
                                  width: 142,
                                  child: Text(accountName,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                          fontSize: 14,
                                          fontWeight: FontWeight.w700)),
                                ),
                                SizedBox(
                                  width: 142,
                                  child: Text(accountEmail,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                          color: AppColors.textMuted,
                                          fontSize: 11)),
                                ),
                              ]),
                        ),
                ),
                if (!collapsed) const Spacer(),
                if (!collapsed)
                  IconButton(
                      tooltip: 'Paramètres',
                      onPressed: () => onSelect(3),
                      icon: const Icon(Icons.settings_outlined,
                          size: 18, color: AppColors.textMuted)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SidebarSection extends StatelessWidget {
  const _SidebarSection(
      {required this.title, required this.expanded, required this.children});
  final String title;
  final bool expanded;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) => Padding(
        padding: EdgeInsets.only(bottom: expanded ? 20 : 4),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 220),
            child: expanded
                ? Padding(
                    key: ValueKey(title),
                    padding: const EdgeInsets.fromLTRB(12, 0, 12, 6),
                    child: Text(title,
                        style: const TextStyle(
                            color: Colors.white24,
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 1.2)))
                : const SizedBox.shrink(),
          ),
          ...children,
        ]),
      );
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
      height: 42,
      padding: EdgeInsets.symmetric(horizontal: widget.expanded ? 12 : 0),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
        border: selected ? Border.all(color: const Color(0x3353A2FF)) : null,
      ),
      child: Row(
        mainAxisAlignment: widget.expanded
            ? MainAxisAlignment.start
            : MainAxisAlignment.center,
        children: [
          Icon(selected ? widget.item.selectedIcon : widget.item.icon,
              color: fg, size: widget.expanded ? 18 : 21),
          AnimatedSwitcher(
            duration: const Duration(milliseconds: 220),
            child: widget.expanded
                ? SizedBox(
                    key: ValueKey(widget.item.label),
                    width: 174,
                    child: Padding(
                        padding: const EdgeInsets.only(left: 12),
                        child: Text(
                          widget.item.label,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: fg,
                            fontWeight:
                                selected ? FontWeight.w700 : FontWeight.w500,
                            fontSize: 14,
                          ),
                        )))
                : const SizedBox.shrink(),
          ),
          if (selected && widget.expanded)
            Container(
                width: 6,
                height: 6,
                decoration: const BoxDecoration(
                    color: Color(0xFF60A5FA), shape: BoxShape.circle)),
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
  const _Avatar({required this.initials});

  final String initials;

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
      child: Text(initials,
          style: const TextStyle(
              color: Colors.white, fontWeight: FontWeight.w800)),
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
