import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../projects/project_workspace_state.dart';

class _Suggestion {
  const _Suggestion({required this.label, required this.prompt});
  final String label;
  final String prompt;
}

class _Msg {
  const _Msg({
    required this.role,
    required this.text,
    this.isPending = false,
    this.isError = false,
  });
  final String role;
  final String text;
  final bool isPending;
  final bool isError;
}

// ─────────────────────────────────────────────────────────────────────────────
// Main ChatPage — redesigned as a modification assistant
// ─────────────────────────────────────────────────────────────────────────────

class ChatPage extends ConsumerStatefulWidget {
  const ChatPage({super.key});

  @override
  ConsumerState<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends ConsumerState<ChatPage> {
  final _controller = TextEditingController();
  final _scroll = ScrollController();
  final List<_Msg> _messages = [];
  bool _sending = false;

  static const _suggestions = [
    _Suggestion(label: 'Changer les couleurs', prompt: 'Je veux changer le schéma de couleurs de mon site.'),
    _Suggestion(label: 'Modifier le titre principal', prompt: 'Je veux modifier le titre principal (hero) de mon site.'),
    _Suggestion(label: 'Réécrire un texte', prompt: 'Je veux réécrire un texte ou une section de mon site.'),
    _Suggestion(label: 'Ajouter une section', prompt: 'Je veux ajouter une nouvelle section à mon site.'),
    _Suggestion(label: 'Changer la police', prompt: 'Je veux changer la typographie de mon site.'),
    _Suggestion(label: 'Améliorer la visibilité Google', prompt: 'Améliore la visibilité de mon site sur Google : titre, description, mots-clés.'),
    _Suggestion(label: 'Vérifier le mobile', prompt: 'Vérifie que mon site s\'affiche bien sur téléphone et améliore-le si besoin.'),
    _Suggestion(label: 'Refaire le site', prompt: 'Refaire entièrement mon site avec les mêmes informations.'),
  ];

  @override
  void initState() {
    super.initState();
    _messages.add(const _Msg(
      role: 'assistant',
      text:
          'Bonjour, je peux t\'aider à améliorer ton site.\n\nTu peux me demander par exemple :\n• Change le ton du texte pour le rendre plus chaleureux\n• Ajoute une section pour présenter mes services\n• Rends la page plus professionnelle\n• Propose un meilleur titre d\'accueil',
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    _scroll.dispose();
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
          role: 'assistant', text: 'Je prépare la modification…', isPending: true));
    });
    _scrollToEnd();

    final projectId = ref.read(currentProjectIdProvider);
    String response;
    bool isError = false;

    try {
      if (projectId == null || projectId.isEmpty) {
        throw StateError('Aucun site actif.');
      }

      // Detect if it's a regeneration request
      final lower = trimmed.toLowerCase();
      if (lower.contains('régénère') ||
          lower.contains('regenere') ||
          lower.contains('refaire') ||
          lower.contains('recommencer')) {
        await ref.read(apiClientProvider).generateSite(projectId);
        response =
            'Ton site est en cours de recréation. Tu pourras voir le résultat dans l\'aperçu dans quelques instants.';
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
            'Cette fonctionnalité n\'est pas encore disponible pour ce site. Essaie de recréer le site depuis l\'onglet Aperçu.';
      } else {
        response = 'Je n\'ai pas pu appliquer cette demande pour le moment. Essaie de la reformuler simplement.';
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
          Expanded(child: _buildChatList()),
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
                colors: [Color(0xFF2563EB), Color(0xFF0EA5E9)],
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
                const Text('Assistant IA',
                    style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w800)),
                Text('Dites-moi ce que vous voulez modifier',
                    style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.48),
                        fontSize: 11)),
              ],
            ),
          ),
          _IconBtn(
            icon: Icons.undo,
            tooltip: 'Annuler la dernière modification',
            onTap: _undo,
          ),
        ],
      ),
    );
  }

  // ── Chat list (messages + suggestions when empty) ─────────────────────────

  Widget _buildChatList() {
    final showSuggestions = _messages.length <= 1;
    return ListView(
      controller: _scroll,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      children: [
        ..._messages.map((m) {
          if (m.role == 'user') return _UserBubble(text: m.text);
          return _AssistantBubble(
              text: m.text, isPending: m.isPending, isError: m.isError);
        }),
        if (showSuggestions) ...[
          const SizedBox(height: 8),
          _buildSuggestions(),
        ],
      ],
    );
  }

  Widget _buildSuggestions() {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      alignment: WrapAlignment.center,
      children: _suggestions.map((s) {
        return GestureDetector(
          onTap: _sending ? null : () => _send(s.prompt),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
            ),
            child: Text(
              s.label,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.75),
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        );
      }).toList(),
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
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Impossible d\'annuler : $e')));
    }
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
                  colors: [Color(0xFF2563EB), Color(0xFF0EA5E9)])
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
