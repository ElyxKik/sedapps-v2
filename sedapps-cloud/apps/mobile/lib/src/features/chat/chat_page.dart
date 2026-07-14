import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../agents/agent_state.dart';
import '../projects/project_workspace_state.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Quick-action model
// ─────────────────────────────────────────────────────────────────────────────

class _QuickAction {
  const _QuickAction(
      {required this.icon,
      required this.label,
      required this.prompt,
      required this.color});
  final IconData icon;
  final String label;
  final String prompt;
  final Color color;
}

// ─────────────────────────────────────────────────────────────────────────────
// Chat state (local to avoid polluting workspace state)
// ─────────────────────────────────────────────────────────────────────────────

class _Msg {
  const _Msg(
      {required this.role,
      required this.text,
      this.isPending = false,
      this.isError = false,
      this.actionType});
  final String role; // 'user' | 'assistant'
  final String text;
  final bool isPending;
  final bool isError;
  final String? actionType; // for icon display
}

// ─────────────────────────────────────────────────────────────────────────────
// Main ChatPage — redesigned as a modification assistant
// ─────────────────────────────────────────────────────────────────────────────

class ChatPage extends ConsumerStatefulWidget {
  const ChatPage({super.key});

  @override
  ConsumerState<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends ConsumerState<ChatPage>
    with SingleTickerProviderStateMixin {
  final _controller = TextEditingController();
  final _scroll = ScrollController();
  late final TabController _tabController;

  final List<_Msg> _messages = [];
  bool _sending = false;

  static const _quickActions = [
    _QuickAction(
      icon: Icons.palette_outlined,
      label: 'Changer les couleurs',
      prompt: 'Je veux changer le schéma de couleurs de mon site.',
      color: Color(0xFF8B5CF6),
    ),
    _QuickAction(
      icon: Icons.title,
      label: 'Modifier le titre principal',
      prompt: 'Je veux modifier le titre principal (hero) de mon site.',
      color: Color(0xFF3B82F6),
    ),
    _QuickAction(
      icon: Icons.edit_note,
      label: 'Réécrire un texte',
      prompt: 'Je veux réécrire un texte ou une section de mon site.',
      color: Color(0xFF06B6D4),
    ),
    _QuickAction(
      icon: Icons.add_box_outlined,
      label: 'Ajouter une section',
      prompt: 'Je veux ajouter une nouvelle section à mon site.',
      color: Color(0xFF10B981),
    ),
    _QuickAction(
      icon: Icons.text_fields,
      label: 'Changer la police',
      prompt: 'Je veux changer la typographie de mon site.',
      color: Color(0xFFF59E0B),
    ),
    _QuickAction(
      icon: Icons.search,
      label: 'Améliorer le SEO',
      prompt: 'Améliore le SEO de mon site : title, description, mots-clés.',
      color: Color(0xFFEF4444),
    ),
    _QuickAction(
      icon: Icons.smartphone,
      label: 'Vérifier le mobile',
      prompt:
          'Vérifie et améliore le responsive design de mon site sur mobile.',
      color: Color(0xFF14B8A6),
    ),
    _QuickAction(
      icon: Icons.auto_fix_high,
      label: 'Régénérer le site',
      prompt: 'Régénère entièrement mon site avec les mêmes informations.',
      color: Color(0xFFEC4899),
    ),
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _messages.add(const _Msg(
      role: 'assistant',
      text:
          'Bonjour ! Je suis votre assistant de modifications.\n\nDites-moi ce que vous souhaitez changer sur votre site : couleurs, textes, sections, SEO… Je m\'occupe du reste.',
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    _scroll.dispose();
    _tabController.dispose();
    super.dispose();
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scroll.hasClients) return;
      _scroll.animateTo(
        _scroll.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOutCubic,
      );
    });
  }

  Future<void> _send(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || _sending) return;
    _controller.clear();

    setState(() {
      _sending = true;
      _messages.add(_Msg(role: 'user', text: trimmed));
      _messages.add(const _Msg(
          role: 'assistant', text: 'Traitement en cours…', isPending: true));
    });
    _scrollToEnd();

    final projectId = ref.read(currentProjectIdProvider);
    String response;
    bool isError = false;

    try {
      if (projectId == null || projectId.isEmpty) {
        throw StateError('Aucun projet actif.');
      }

      // Detect if it's a regeneration request
      final lower = trimmed.toLowerCase();
      if (lower.contains('régénère') ||
          lower.contains('regenere') ||
          lower.contains('refaire') ||
          lower.contains('recommencer')) {
        await ref.read(apiClientProvider).generateSite(projectId);
        response =
            '✅ Régénération lancée ! Votre site est en cours de reconstruction. Allez dans l\'onglet Aperçu dans quelques instants.';
      } else {
        // Use edit_chat endpoint — the real modification API
        final result = await ref.read(apiClientProvider).editChat(
              projectId,
              'global',
              trimmed,
              {
                'context': 'user_modification_request',
                'history': _messages
                    .where((m) => !m.isPending && m.role == 'user')
                    .take(5)
                    .map((m) => m.text)
                    .toList(),
              },
            );
        response = (result['message'] ?? result['response'] ?? '').toString();
        if (response.trim().isEmpty) {
          response =
              '✅ Modification appliquée ! Rechargez l\'aperçu pour voir le résultat.';
        }
        // Refresh project state
        final data = await ref.read(apiClientProvider).project(projectId);
        if (mounted) {
          ref.read(projectWorkspaceProvider.notifier).syncFromProject(data);
        }
      }
    } catch (e) {
      final msg = e.toString();
      if (msg.contains('404') || msg.contains('not found')) {
        response =
            'Cette fonctionnalité n\'est pas encore disponible pour ce projet. Essayez de régénérer le site depuis l\'onglet Aperçu.';
      } else {
        response = 'Erreur : $msg';
        isError = true;
      }
    }

    if (!mounted) return;
    setState(() {
      _sending = false;
      final idx = _messages.lastIndexWhere((m) => m.isPending);
      if (idx >= 0) {
        _messages[idx] = _Msg(
            role: 'assistant', text: response, isError: isError);
      }
    });
    _scrollToEnd();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF0A0F1E), Color(0xFF0F172A)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Column(
        children: [
          _buildHeader(),
          _buildTabBar(),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildQuickActionsTab(),
                _buildChatTab(),
              ],
            ),
          ),
          _buildComposer(),
        ],
      ),
    );
  }

  // ── Header ────────────────────────────────────────────────────────────────

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
      decoration: BoxDecoration(
        border: Border(
            bottom: BorderSide(color: Colors.white.withValues(alpha: 0.08))),
      ),
      child: Row(
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF2563EB), Color(0xFF7C3AED)],
              ),
              borderRadius: BorderRadius.circular(13),
              boxShadow: [
                BoxShadow(
                    color: const Color(0xFF2563EB).withValues(alpha: 0.4),
                    blurRadius: 16,
                    offset: const Offset(0, 6)),
              ],
            ),
            child: const Icon(Icons.auto_fix_high, color: Colors.white, size: 21),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Assistant de modifications',
                    style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w800)),
                Text('Dites-moi ce que vous voulez changer',
                    style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.48),
                        fontSize: 11)),
              ],
            ),
          ),
          // Undo button
          _IconBtn(
            icon: Icons.undo,
            tooltip: 'Annuler la dernière modification',
            onTap: _undo,
          ),
        ],
      ),
    );
  }

  // ── Tabs ──────────────────────────────────────────────────────────────────

  Widget _buildTabBar() {
    return Container(
      decoration: BoxDecoration(
        border: Border(
            bottom: BorderSide(color: Colors.white.withValues(alpha: 0.07))),
      ),
      child: TabBar(
        controller: _tabController,
        labelColor: AppColors.skyBlueAccent,
        unselectedLabelColor: Colors.white.withValues(alpha: 0.45),
        indicatorColor: AppColors.skyBlue,
        indicatorSize: TabBarIndicatorSize.label,
        labelStyle:
            const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
        tabs: const [
          Tab(text: '⚡  Actions rapides'),
          Tab(text: '💬  Conversation'),
        ],
      ),
    );
  }

  // ── Quick actions tab ─────────────────────────────────────────────────────

  Widget _buildQuickActionsTab() {
    return ListView(
      padding: const EdgeInsets.all(18),
      children: [
        Text('Que souhaitez-vous modifier ?',
            style: TextStyle(
                color: Colors.white.withValues(alpha: 0.55),
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.5)),
        const SizedBox(height: 14),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
            maxCrossAxisExtent: 200,
            mainAxisExtent: 90,
            crossAxisSpacing: 10,
            mainAxisSpacing: 10,
          ),
          itemCount: _quickActions.length,
          itemBuilder: (context, i) => _QuickActionCard(
            action: _quickActions[i],
            onTap: () {
              _tabController.animateTo(1); // Switch to chat tab
              _send(_quickActions[i].prompt);
            },
          ),
        ),
        const SizedBox(height: 24),
        _RegenerateCard(
          onTap: () => _send(
              'Régénère entièrement mon site avec les mêmes informations de marque.'),
        ),
        const SizedBox(height: 16),
        _HintCard(),
      ],
    );
  }

  // ── Chat tab ──────────────────────────────────────────────────────────────

  Widget _buildChatTab() {
    return ListView.builder(
      controller: _scroll,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      itemCount: _messages.length,
      itemBuilder: (context, i) {
        final m = _messages[i];
        if (m.role == 'user') return _UserBubble(text: m.text);
        return _AssistantBubble(
            text: m.text, isPending: m.isPending, isError: m.isError);
      },
    );
  }

  // ── Composer ──────────────────────────────────────────────────────────────

  Widget _buildComposer() {
    final active = _controller.text.trim().isNotEmpty;
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 10, 14, 16),
      decoration: BoxDecoration(
        border: Border(
            top: BorderSide(color: Colors.white.withValues(alpha: 0.08))),
      ),
      child: SafeArea(
        top: false,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 780),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 160),
              padding: const EdgeInsets.fromLTRB(16, 6, 6, 6),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.06),
                borderRadius: BorderRadius.circular(22),
                border: Border.all(
                  color: active
                      ? AppColors.skyBlue.withValues(alpha: 0.6)
                      : Colors.white.withValues(alpha: 0.10),
                  width: active ? 1.5 : 1,
                ),
                boxShadow: active
                    ? [
                        BoxShadow(
                            color: AppColors.skyBlue.withValues(alpha: 0.14),
                            blurRadius: 20,
                            offset: const Offset(0, 6))
                      ]
                    : null,
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      minLines: 1,
                      maxLines: 4,
                      style: const TextStyle(
                          color: Colors.white, fontSize: 14),
                      decoration: InputDecoration(
                        hintText: _sending
                            ? 'Modification en cours…'
                            : 'Décrivez votre modification…',
                        hintStyle: TextStyle(
                            color: Colors.white.withValues(alpha: 0.35),
                            fontSize: 14),
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        filled: false,
                        contentPadding:
                            const EdgeInsets.symmetric(vertical: 11),
                      ),
                      onChanged: (_) => setState(() {}),
                      onSubmitted: _sending ? null : _send,
                    ),
                  ),
                  const SizedBox(width: 8),
                  _SendBtn(
                    active: active && !_sending,
                    sending: _sending,
                    onTap: () => _send(_controller.text),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  Future<void> _undo() async {
    final projectId = ref.read(currentProjectIdProvider);
    if (projectId == null) return;
    try {
      await ref.read(apiClientProvider).undoEdit(projectId);
      if (!mounted) return;
      setState(() {
        _messages.add(const _Msg(
            role: 'assistant',
            text: '↩️ Dernière modification annulée. Rechargez l\'aperçu.'));
      });
      _scrollToEnd();
      _tabController.animateTo(1);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Impossible d\'annuler : $e')));
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Quick action card
// ─────────────────────────────────────────────────────────────────────────────

class _QuickActionCard extends StatefulWidget {
  const _QuickActionCard({required this.action, required this.onTap});
  final _QuickAction action;
  final VoidCallback onTap;

  @override
  State<_QuickActionCard> createState() => _QuickActionCardState();
}

class _QuickActionCardState extends State<_QuickActionCard> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 160),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: _hovered
                ? widget.action.color.withValues(alpha: 0.16)
                : Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: _hovered
                  ? widget.action.color.withValues(alpha: 0.55)
                  : Colors.white.withValues(alpha: 0.09),
              width: _hovered ? 1.5 : 1,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: widget.action.color.withValues(alpha: 0.20),
                  borderRadius: BorderRadius.circular(9),
                ),
                child: Icon(widget.action.icon,
                    color: widget.action.color, size: 17),
              ),
              Text(
                widget.action.label,
                style: TextStyle(
                  color: _hovered
                      ? Colors.white
                      : Colors.white.withValues(alpha: 0.80),
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  height: 1.3,
                ),
                maxLines: 2,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Regenerate card (prominent)
// ─────────────────────────────────────────────────────────────────────────────

class _RegenerateCard extends StatelessWidget {
  const _RegenerateCard({required this.onTap});
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1E293B), Color(0xFF0F172A)],
          ),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
              color: const Color(0xFF7C3AED).withValues(alpha: 0.35)),
          boxShadow: [
            BoxShadow(
                color: const Color(0xFF7C3AED).withValues(alpha: 0.12),
                blurRadius: 24,
                offset: const Offset(0, 8)),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 46,
              height: 46,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                    colors: [Color(0xFF2563EB), Color(0xFF7C3AED)]),
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Icon(Icons.rocket_launch,
                  color: Colors.white, size: 22),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Régénérer le site',
                      style: TextStyle(
                          color: Colors.white,
                          fontSize: 15,
                          fontWeight: FontWeight.w800)),
                  const SizedBox(height: 3),
                  Text(
                    'Relance la génération complète avec votre brief.',
                    style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.50),
                        fontSize: 12),
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right,
                color: Colors.white.withValues(alpha: 0.35)),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Hint card
// ─────────────────────────────────────────────────────────────────────────────

class _HintCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.skyBlue.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(14),
        border:
            Border.all(color: AppColors.skyBlue.withValues(alpha: 0.18)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Icon(Icons.tips_and_updates_outlined,
                color: AppColors.skyBlueAccent, size: 15),
            const SizedBox(width: 6),
            Text('Exemples de demandes',
                style: TextStyle(
                    color: AppColors.skyBlueAccent,
                    fontSize: 12,
                    fontWeight: FontWeight.w700)),
          ]),
          const SizedBox(height: 10),
          ...[
            '"Mets la couleur principale en vert émeraude"',
            '"Réécris le titre du hero de manière plus percutante"',
            '"Ajoute une section témoignages clients"',
            '"Améliore la meta description pour le SEO"',
          ].map((hint) => Padding(
                padding: const EdgeInsets.only(bottom: 5),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('›  ',
                        style: TextStyle(
                            color: AppColors.skyBlue, fontSize: 12)),
                    Expanded(
                      child: Text(hint,
                          style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.60),
                              fontSize: 12,
                              fontStyle: FontStyle.italic)),
                    ),
                  ],
                ),
              )),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Bubbles
// ─────────────────────────────────────────────────────────────────────────────

class _UserBubble extends StatelessWidget {
  const _UserBubble({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Align(
        alignment: Alignment.centerRight,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF2563EB), Color(0xFF4F46E5)],
              ),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(18),
                topRight: Radius.circular(18),
                bottomLeft: Radius.circular(18),
                bottomRight: Radius.circular(4),
              ),
              boxShadow: [
                BoxShadow(
                    color: const Color(0xFF2563EB).withValues(alpha: 0.30),
                    blurRadius: 14,
                    offset: const Offset(0, 6)),
              ],
            ),
            child: Text(text,
                style: const TextStyle(
                    color: Colors.white, fontSize: 14, height: 1.45)),
          ),
        ),
      ),
    );
  }
}

class _AssistantBubble extends StatelessWidget {
  const _AssistantBubble(
      {required this.text,
      this.isPending = false,
      this.isError = false});
  final String text;
  final bool isPending;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Align(
        alignment: Alignment.centerLeft,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: isError
                  ? const Color(0xFFEF4444).withValues(alpha: 0.08)
                  : Colors.white.withValues(alpha: 0.06),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(4),
                topRight: Radius.circular(18),
                bottomLeft: Radius.circular(18),
                bottomRight: Radius.circular(18),
              ),
              border: Border.all(
                color: isError
                    ? const Color(0xFFEF4444).withValues(alpha: 0.35)
                    : Colors.white.withValues(alpha: 0.09),
              ),
            ),
            child: isPending
                ? Row(mainAxisSize: MainAxisSize.min, children: [
                    const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: AppColors.skyBlue)),
                    const SizedBox(width: 10),
                    Text(text,
                        style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.50),
                            fontSize: 13)),
                  ])
                : SelectableText(
                    text,
                    style: TextStyle(
                        color: isError
                            ? const Color(0xFFEF4444)
                            : Colors.white.withValues(alpha: 0.90),
                        fontSize: 14,
                        height: 1.5),
                  ),
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Send button
// ─────────────────────────────────────────────────────────────────────────────

class _SendBtn extends StatelessWidget {
  const _SendBtn(
      {required this.active, required this.sending, required this.onTap});
  final bool active;
  final bool sending;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: active ? onTap : null,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: active
              ? const LinearGradient(
                  colors: [Color(0xFF2563EB), Color(0xFF7C3AED)])
              : null,
          color: active ? null : Colors.white.withValues(alpha: 0.08),
          boxShadow: active
              ? [
                  BoxShadow(
                      color: const Color(0xFF2563EB).withValues(alpha: 0.40),
                      blurRadius: 14,
                      offset: const Offset(0, 5))
                ]
              : null,
        ),
        child: Center(
          child: sending
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: Colors.white))
              : Icon(Icons.arrow_upward_rounded,
                  color: active
                      ? Colors.white
                      : Colors.white.withValues(alpha: 0.30),
                  size: 20),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Icon button helper
// ─────────────────────────────────────────────────────────────────────────────

class _IconBtn extends StatelessWidget {
  const _IconBtn(
      {required this.icon, required this.tooltip, required this.onTap});
  final IconData icon;
  final String tooltip;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: tooltip,
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.06),
            borderRadius: BorderRadius.circular(10),
            border:
                Border.all(color: Colors.white.withValues(alpha: 0.10)),
          ),
          child:
              Icon(icon, color: Colors.white.withValues(alpha: 0.55), size: 18),
        ),
      ),
    );
  }
}
