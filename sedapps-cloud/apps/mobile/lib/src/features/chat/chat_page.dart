import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme.dart';
import '../agents/agent_models.dart';
import '../agents/agent_state.dart';
import '../projects/project_workspace_state.dart';

/// Page Générateur IA — chat conversationnel avec contexte du projet,
/// affichage des tools / agents utilisés et de la timeline de génération.
class ChatPage extends ConsumerStatefulWidget {
  const ChatPage({super.key});

  @override
  ConsumerState<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends ConsumerState<ChatPage> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  bool _canSend = false;
  bool _sending = false;

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty || _sending) return;
    _controller.clear();
    setState(() {
      _canSend = false;
      _sending = true;
    });
    await ref.read(projectWorkspaceProvider.notifier).askAi(text);
    if (!mounted) return;
    setState(() => _sending = false);
    _scrollToEnd();
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 280),
        curve: Curves.easeOutCubic,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final jobAsync = ref.watch(currentJobProvider);
    final messages = ref.watch(projectWorkspaceProvider.select((s) => s.messages));
    ref.listen<List<ChatMessage>>(
      projectWorkspaceProvider.select((s) => s.messages),
      (_, __) => _scrollToEnd(),
    );

    return Container(
      decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
      child: Column(
        children: [
          const _GeneratorHeader(),
          Expanded(
            child: jobAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Erreur: $e', style: const TextStyle(color: AppColors.textPrimary))),
              data: (job) => _MessagesList(
                job: job,
                messages: messages,
                scrollController: _scrollController,
                onSuggestion: (s) {
                  _controller.text = s;
                  setState(() => _canSend = true);
                },
              ),
            ),
          ),
          _Composer(
            controller: _controller,
            canSend: _canSend && !_sending,
            sending: _sending,
            onChanged: (v) => setState(() => _canSend = v.trim().isNotEmpty),
            onSend: _send,
          ),
        ],
      ),
    );
  }
}

class _GeneratorHeader extends StatelessWidget {
  const _GeneratorHeader();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 14),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.borderSoft)),
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              gradient: AppColors.heroGradient,
              borderRadius: BorderRadius.circular(14),
              boxShadow: [BoxShadow(color: AppColors.primary.withValues(alpha: 0.35), blurRadius: 18, offset: const Offset(0, 8))],
            ),
            child: const Icon(Icons.auto_awesome, color: Colors.white, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    const Text('Générateur IA', style: TextStyle(color: AppColors.textPrimary, fontSize: 18, fontWeight: FontWeight.w800)),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(color: AppColors.violet.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(8)),
                      child: const Text('DeepSeek', style: TextStyle(color: AppColors.violet, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 0.4)),
                    ),
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  'Multi-agents · contexte projet en mémoire',
                  style: TextStyle(color: AppColors.textPrimary.withValues(alpha: 0.6), fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MessagesList extends StatelessWidget {
  const _MessagesList({
    required this.job,
    required this.messages,
    required this.scrollController,
    required this.onSuggestion,
  });

  final AiJobView? job;
  final List<ChatMessage> messages;
  final ScrollController scrollController;
  final ValueChanged<String> onSuggestion;

  static const _suggestions = [
    'Change la couleur principale en violet',
    'Réécris le hero avec un ton plus dynamique',
    'Optimise le SEO pour les requêtes locales',
    'Crée un article de blog sur nos services',
  ];

  @override
  Widget build(BuildContext context) {
    final showSuggestions = messages.length <= 1 && (job == null || job!.agents.isEmpty);
    return ListView(
      controller: scrollController,
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 16),
      children: [
        for (final m in messages) ...[
          if (m.role == 'user') _UserBubble(text: m.text) else _AssistantBubble(message: m),
          const SizedBox(height: 12),
        ],
        if (job != null && job!.agents.isNotEmpty) _GenerationTimeline(job: job!),
        if (showSuggestions) ...[
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Text('Idées rapides', style: TextStyle(color: AppColors.textPrimary.withValues(alpha: 0.55), fontSize: 12, fontWeight: FontWeight.w700, letterSpacing: 0.6)),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final s in _suggestions)
                InkWell(
                  onTap: () => onSuggestion(s),
                  borderRadius: BorderRadius.circular(999),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.06),
                      borderRadius: BorderRadius.circular(999),
                      border: Border.all(color: AppColors.borderSoft),
                    ),
                    child: Text(s, style: const TextStyle(color: AppColors.textPrimary, fontSize: 13)),
                  ),
                ),
            ],
          ),
        ],
      ],
    );
  }
}

class _UserBubble extends StatelessWidget {
  const _UserBubble({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerRight,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 600),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            gradient: const LinearGradient(colors: [AppColors.primary, AppColors.primaryLight]),
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(18),
              topRight: Radius.circular(18),
              bottomLeft: Radius.circular(18),
              bottomRight: Radius.circular(4),
            ),
            boxShadow: [BoxShadow(color: AppColors.primary.withValues(alpha: 0.3), blurRadius: 14, offset: const Offset(0, 6))],
          ),
          child: Text(text, style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.4)),
        ),
      ),
    );
  }
}

class _AssistantBubble extends StatelessWidget {
  const _AssistantBubble({required this.message});
  final ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final borderColor = message.isError ? AppColors.danger.withValues(alpha: 0.5) : AppColors.borderSoft;
    return Align(
      alignment: Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 720),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.06),
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(4),
              topRight: Radius.circular(18),
              bottomLeft: Radius.circular(18),
              bottomRight: Radius.circular(18),
            ),
            border: Border.all(color: borderColor),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 8,
                runSpacing: 6,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  Container(
                    width: 26,
                    height: 26,
                    decoration: BoxDecoration(
                      gradient: AppColors.heroGradient,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.auto_awesome, color: Colors.white, size: 14),
                  ),
                  const Text('Générateur IA', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w700, fontSize: 13)),
                  if (message.isPending) ...[
                    const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primaryLight)),
                    Text('réflexion…', style: TextStyle(color: AppColors.textPrimary.withValues(alpha: 0.5), fontSize: 11)),
                  ],
                ],
              ),
              if (message.agents.isNotEmpty || message.tools.isNotEmpty) ...[
                const SizedBox(height: 10),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    for (final a in message.agents)
                      _ChipTag(label: a, icon: Icons.smart_toy_outlined, color: AppColors.primaryLight),
                    for (final t in message.tools)
                      _ChipTag(label: t, icon: Icons.build_outlined, color: AppColors.violet),
                  ],
                ),
              ],
              if (!message.isPending) ...[
                const SizedBox(height: 12),
                SelectableText(
                  message.text,
                  style: TextStyle(
                    color: message.isError ? AppColors.danger : AppColors.textPrimary,
                    fontSize: 14,
                    height: 1.5,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _ChipTag extends StatelessWidget {
  const _ChipTag({required this.label, required this.icon, required this.color});
  final String label;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 12),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

class _GenerationTimeline extends StatelessWidget {
  const _GenerationTimeline({required this.job});
  final AiJobView job;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 6),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.borderSoft),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              const Icon(Icons.timeline, color: AppColors.violet, size: 18),
              const Text('Pipeline de génération', style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w700, fontSize: 13)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: job.status == 'success'
                      ? AppColors.success.withValues(alpha: 0.18)
                      : job.status == 'failed' || job.status == 'error'
                          ? AppColors.danger.withValues(alpha: 0.18)
                          : AppColors.warning.withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  job.status,
                  style: TextStyle(
                    color: job.status == 'success'
                        ? AppColors.success
                        : job.status == 'failed' || job.status == 'error'
                            ? AppColors.danger
                            : AppColors.warning,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          for (var i = 0; i < job.agents.length; i++) ...[
            _AgentRow(agent: job.agents[i], index: i + 1),
            if (i < job.agents.length - 1) const SizedBox(height: 8),
          ],
        ],
      ),
    );
  }
}

class _AgentRow extends StatelessWidget {
  const _AgentRow({required this.agent, required this.index});
  final AgentRunView agent;
  final int index;

  @override
  Widget build(BuildContext context) {
    final ok = agent.status == 'ok' || agent.status == 'success';
    final color = ok ? AppColors.success : agent.status == 'running' ? AppColors.warning : AppColors.danger;
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.borderSoft),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(color: color.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(8)),
                child: Icon(_iconFor(agent.name), color: color, size: 16),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_labelFor(agent.name), style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w700, fontSize: 13)),
                    Text('#$index · ${agent.durationMs}ms · ${agent.tokensIn}↗ ${agent.tokensOut}↘',
                        style: TextStyle(color: AppColors.textPrimary.withValues(alpha: 0.5), fontSize: 10)),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(color: color.withValues(alpha: 0.18), borderRadius: BorderRadius.circular(6)),
                child: Text(agent.status, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w700)),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(_summary(agent), style: TextStyle(color: AppColors.textPrimary.withValues(alpha: 0.75), fontSize: 12, height: 1.4)),
          if (agent.warnings.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text('⚠ ${agent.warnings.join(', ')}', style: const TextStyle(color: AppColors.warning, fontSize: 11)),
            ),
          if ((agent.output).isNotEmpty)
            Theme(
              data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                tilePadding: EdgeInsets.zero,
                childrenPadding: const EdgeInsets.only(top: 4, bottom: 6),
                iconColor: AppColors.textPrimary.withValues(alpha: 0.5),
                collapsedIconColor: AppColors.textPrimary.withValues(alpha: 0.5),
                title: const Text('JSON', style: TextStyle(color: AppColors.primaryLight, fontSize: 11, fontWeight: FontWeight.w600)),
                children: [
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(color: Colors.black.withValues(alpha: 0.4), borderRadius: BorderRadius.circular(8)),
                    child: SelectableText(
                      const JsonEncoder.withIndent('  ').convert(agent.output),
                      style: const TextStyle(color: Colors.white, fontFamily: 'monospace', fontSize: 10),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  IconData _iconFor(String name) {
    if (name.contains('design')) return Icons.palette;
    if (name.contains('copy') || name.contains('writer')) return Icons.edit_note;
    if (name.contains('redacteur') || name.contains('rédact')) return Icons.article;
    if (name.contains('seo')) return Icons.search;
    if (name.contains('frontend') || name.contains('dev')) return Icons.code;
    if (name.contains('editeur') || name.contains('édit')) return Icons.fact_check;
    return Icons.smart_toy;
  }

  String _labelFor(String name) {
    return name.replaceAll('_', ' ').split(' ').map((w) => w.isEmpty ? w : w[0].toUpperCase() + w.substring(1)).join(' ');
  }

  String _summary(AgentRunView a) {
    final out = a.output;
    if (a.name.contains('design')) {
      final tokens = out['design_tokens'] ?? out['tokens'];
      if (tokens is Map) {
        final primary = tokens['primary'] ?? tokens['primary_color'];
        if (primary != null) return 'Palette générée · primary $primary';
      }
      return 'Design tokens et layout définis.';
    }
    if (a.name.contains('copy')) return out['hero_title']?.toString() ?? 'Copy rédigée.';
    if (a.name.contains('redact')) return 'Sections rédigées (${(out['sections'] as List?)?.length ?? '?'} blocs).';
    if (a.name.contains('seo')) return out['meta_title']?.toString() ?? 'SEO optimisé.';
    if (a.name.contains('frontend') || a.name.contains('dev')) return 'HTML/CSS/JS produits.';
    if (a.name.contains('editeur') || a.name.contains('édit')) return 'Revue et corrections finales.';
    return 'Tâche complétée.';
  }
}

class _Composer extends StatelessWidget {
  const _Composer({
    required this.controller,
    required this.canSend,
    required this.sending,
    required this.onChanged,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool canSend;
  final bool sending;
  final ValueChanged<String> onChanged;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 10, 14, 14),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: AppColors.borderSoft)),
      ),
      child: SafeArea(
        top: false,
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 860),
            child: Container(
              padding: const EdgeInsets.fromLTRB(16, 6, 6, 6),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.06),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: canSend ? AppColors.primary.withValues(alpha: 0.5) : AppColors.borderSoft),
                boxShadow: canSend
                    ? [BoxShadow(color: AppColors.primary.withValues(alpha: 0.18), blurRadius: 22, offset: const Offset(0, 8))]
                    : null,
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Padding(
                    padding: const EdgeInsets.only(top: 12, right: 8),
                    child: Icon(Icons.auto_awesome, color: canSend ? AppColors.primaryLight : AppColors.textMuted, size: 18),
                  ),
                  Expanded(
                    child: TextField(
                      controller: controller,
                      minLines: 1,
                      maxLines: 5,
                      onChanged: onChanged,
                      style: const TextStyle(color: AppColors.textPrimary, fontSize: 14),
                      decoration: InputDecoration(
                        hintText: sending ? 'Génération en cours…' : 'Demande une modification, un article, une couleur…',
                        hintStyle: TextStyle(color: AppColors.textPrimary.withValues(alpha: 0.4)),
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        filled: false,
                        contentPadding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  _SendButton(canSend: canSend, sending: sending, onSend: onSend),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _SendButton extends StatelessWidget {
  const _SendButton({required this.canSend, required this.sending, required this.onSend});
  final bool canSend;
  final bool sending;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      width: 42,
      height: 42,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: canSend ? AppColors.heroGradient : null,
        color: canSend ? null : Colors.white.withValues(alpha: 0.08),
        boxShadow: canSend
            ? [BoxShadow(color: AppColors.primary.withValues(alpha: 0.4), blurRadius: 16, offset: const Offset(0, 6))]
            : null,
      ),
      child: Material(
        color: Colors.transparent,
        shape: const CircleBorder(),
        child: InkWell(
          customBorder: const CircleBorder(),
          onTap: canSend ? onSend : null,
          child: Center(
            child: sending
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : Icon(Icons.arrow_upward_rounded, color: canSend ? Colors.white : AppColors.textMuted, size: 22),
          ),
        ),
      ),
    );
  }
}
