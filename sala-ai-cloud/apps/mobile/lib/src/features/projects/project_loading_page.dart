import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/api_client.dart';
import '../agents/agent_state.dart';

class ProjectLoadingPage extends ConsumerStatefulWidget {
  final String projectId;
  final String projectName;

  const ProjectLoadingPage({
    required this.projectId,
    required this.projectName,
    super.key,
  });

  @override
  ConsumerState<ProjectLoadingPage> createState() => _ProjectLoadingPageState();
}

class _LiveStep {
  _LiveStep({
    required this.step,
    required this.label,
    required this.status,
    required this.progress,
  });

  final String step;
  String label;
  String status; // running, ok, failed
  int progress;
}

class _ProjectLoadingPageState extends ConsumerState<ProjectLoadingPage>
    with SingleTickerProviderStateMixin {
  late final AnimationController _animationController;
  Timer? _pollTimer;
  final Map<String, _LiveStep> _steps = {};
  final List<String> _stepOrder = [];
  int _progress = 0;
  String _currentLabel = 'Ton site est en cours de création…';
  bool _navigating = false;

  static const _waitMessages = [
    'Sala AI analyse ton activité…',
    'Choix des couleurs et de la typographie…',
    'Construction de la structure de ton site…',
    'Rédaction des textes adaptés à ton activité…',
    'Optimisation pour Google…',
    'Assemblage de chaque section…',
    'Finitions du design…',
    'Presque terminé — encore quelques secondes…',
  ];
  int _waitMsgIndex = 0;
  Timer? _msgTimer;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat();
    _startPolling();
    _msgTimer = Timer.periodic(const Duration(seconds: 4), (_) {
      if (mounted) setState(() => _waitMsgIndex = (_waitMsgIndex + 1) % _waitMessages.length);
    });
  }

  void _startPolling() {
    final jobId = ref.read(currentJobIdProvider);
    if (jobId == null) return;
    _pollTimer = Timer.periodic(const Duration(milliseconds: 1200), (_) async {
      try {
        final job = await ref.read(apiClientProvider).job(jobId);
        if (!mounted) return;
        final input = job['input'] as Map<String, dynamic>? ?? {};
        final events = (input['events'] as List?) ?? [];
        for (final raw in events) {
          if (raw is! Map) continue;
          final step = (raw['step'] ?? '').toString();
          if (step.isEmpty) continue;
          final label = (raw['label'] ?? '').toString();
          final status = (raw['status'] ?? 'running').toString();
          final progress = (raw['progress'] as num?)?.toInt() ?? 0;
          final existing = _steps[step];
          if (existing == null) {
            _steps[step] = _LiveStep(
                step: step, label: label, status: status, progress: progress);
            _stepOrder.add(step);
          } else {
            existing.label = label;
            existing.status = status;
            existing.progress = progress;
          }
          if (progress > _progress) _progress = progress;
          if (status == 'running') _currentLabel = label;
        }
        // Marquer les étapes précédentes comme ok dès qu'une nouvelle est running
        for (var i = 0; i < _stepOrder.length - 1; i++) {
          final s = _steps[_stepOrder[i]]!;
          if (s.status == 'running') s.status = 'ok';
        }
        setState(() {});

        final status = job['status'] as String?;
        if ((status == 'success' || status == 'degraded') && !_navigating) {
          _navigating = true;
          _pollTimer?.cancel();
          await Future.delayed(const Duration(milliseconds: 400));
          if (mounted) context.go('/projects/${widget.projectId}');
        } else if (status == 'failed' && !_navigating) {
          _navigating = true;
          _pollTimer?.cancel();
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                  content:
                      Text('La création n\'a pas abouti. Réessaie dans un instant.')),
            );
          }
        }
      } catch (_) {
        // ignore transient errors
      }
    });
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _msgTimer?.cancel();
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: Padding(
              padding: const EdgeInsets.all(28),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _buildHeader(),
                  const SizedBox(height: 32),
                  _buildProgressBar(),
                  const SizedBox(height: 8),
                  Text(
                    _currentLabel,
                    style: const TextStyle(color: Colors.white70, fontSize: 13),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 32),
                  Flexible(child: _buildStepsList()),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      children: [
        ScaleTransition(
          scale: Tween<double>(begin: 0.85, end: 1.15).animate(
            CurvedAnimation(
                parent: _animationController, curve: Curves.easeInOut),
          ),
          child: Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: const LinearGradient(
                colors: [Color(0xFF2563EB), Color(0xFF0EA5E9)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF2563EB).withOpacity(0.5),
                  blurRadius: 20,
                  spreadRadius: 4,
                ),
              ],
            ),
            child:
                const Icon(Icons.auto_awesome, color: Colors.white, size: 36),
          ),
        ),
        const SizedBox(height: 20),
        Text(
          'Création de ${widget.projectName}',
          style: const TextStyle(
              color: Colors.white, fontSize: 22, fontWeight: FontWeight.w700),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 6),
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 600),
          child: Text(
            _waitMessages[_waitMsgIndex],
            key: ValueKey(_waitMsgIndex),
            style: const TextStyle(color: Colors.white54, fontSize: 13),
            textAlign: TextAlign.center,
          ),
        ),
      ],
    );
  }

  Widget _buildProgressBar() {
    return ClipRRect(
      borderRadius: BorderRadius.circular(8),
      child: LinearProgressIndicator(
        minHeight: 6,
        value: _progress > 0 ? _progress / 100 : null,
        backgroundColor: Colors.white10,
        valueColor: AlwaysStoppedAnimation<Color>(
            const Color(0xFF22D3EE).withOpacity(0.9)),
      ),
    );
  }

  Widget _buildStepsList() {
    if (_stepOrder.isEmpty) {
      return const SizedBox.shrink();
    }
    return ListView.builder(
      shrinkWrap: true,
      itemCount: _stepOrder.length,
      itemBuilder: (context, index) {
        final s = _steps[_stepOrder[index]]!;
        return _buildStepRow(s);
      },
    );
  }

  String _friendlyLabel(String label, String step) {
    // Si le backend envoie un label non vide, on l'utilise
    if (label.isNotEmpty) return label;
    // Fallback : mapper le nom technique vers un texte lisible
    const fallbacks = {
      'flow_select': 'Préparation de ton site…',
      'designer': 'Création de ton identité visuelle…',
      'copywriter': 'Rédaction des textes de ton site…',
      'seo': 'Optimisation pour Google…',
      'form_builder': 'Mise en place du formulaire de contact…',
      'cms_builder': 'Organisation du contenu…',
      'site_planner': 'Planification des pages…',
      'static_page_builder': 'Construction des pages…',
      'static_frontend_builder': 'Assemblage du site…',
      'animation_director': 'Ajout des animations…',
      'analytics_setup': 'Configuration des statistiques…',
      'strategy_director': 'Définition de la stratégie…',
      'ux_architect': 'Optimisation de l\'expérience visiteur…',
      'premium_qa': 'Contrôle qualité avancé…',
      'refinement_agent': 'Finitions de ton site…',
      'qa': 'Vérification qualité…',
      'frontend_builder': 'Construction de l\'interface…',
      'frontend_generator': 'Assemblage des composants…',
      'blog_writer': 'Rédaction des articles…',
    };
    return fallbacks[step] ?? 'Ton site est en cours de création…';
  }

  Widget _buildStepRow(_LiveStep s) {
    IconData icon;
    Color color;
    Widget? trailing;
    switch (s.status) {
      case 'ok':
        icon = Icons.check_circle;
        color = const Color(0xFF22C55E);
        break;
      case 'failed':
        icon = Icons.error;
        color = const Color(0xFFEF4444);
        break;
      default:
        icon = Icons.radio_button_unchecked;
        color = const Color(0xFF22D3EE);
        trailing = const SizedBox(
          width: 14,
          height: 14,
          child: CircularProgressIndicator(
              strokeWidth: 2, color: Color(0xFF22D3EE)),
        );
    }
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 18),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              _friendlyLabel(s.label, s.step),
              style: const TextStyle(color: Colors.white, fontSize: 13),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (trailing != null) ...[const SizedBox(width: 8), trailing],
        ],
      ),
    );
  }
}
