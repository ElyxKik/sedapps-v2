import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/theme.dart';
import '../features/agents/agent_state.dart';

/// Mappe le nom technique d'un agent vers un message marketing lisible.
String _friendlyAgentMessage(String name) {
  const map = {
    'flow_select': 'Sélection de la stratégie…',
    'designer': 'Création de ton identité visuelle…',
    'copywriter': 'Rédaction des textes…',
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
  return map[name] ?? 'Ton site est en cours de création…';
}

/// Bannière compacte de génération en cours — affichée sur toutes les pages
/// tant qu'un job est actif dans currentJobIdProvider.
class ActiveJobBanner extends ConsumerWidget {
  const ActiveJobBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final jobId = ref.watch(currentJobIdProvider);
    final projectId = ref.watch(currentJobProjectIdProvider);

    if (jobId == null || projectId == null) return const SizedBox.shrink();

    final projectAsync = ref.watch(currentJobProjectProvider);
    final jobAsync = ref.watch(currentJobProvider);

    return projectAsync.when(
      data: (project) {
        if (project == null) return const SizedBox.shrink();

        final projectName = project['name']?.toString() ?? 'Ton site';

        // Message de progression
        String progressMessage = 'Ton site est en cours de création…';
        jobAsync.whenData((job) {
          if (job != null && job.agents.isNotEmpty) {
            final running = job.agents
                .where((a) => a.status == 'running')
                .toList();
            if (running.isNotEmpty) {
              progressMessage = _friendlyAgentMessage(running.last.name);
            }
          }
        });

        return _GenerationBanner(
          projectName: projectName,
          progressMessage: progressMessage,
          onTap: () => context.go('/projects/${project['id']}'),
        );
      },
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
    );
  }
}

class _GenerationBanner extends StatefulWidget {
  const _GenerationBanner({
    required this.projectName,
    required this.progressMessage,
    required this.onTap,
  });

  final String projectName;
  final String progressMessage;
  final VoidCallback onTap;

  @override
  State<_GenerationBanner> createState() => _GenerationBannerState();
}

class _GenerationBannerState extends State<_GenerationBanner>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse;
  late final Animation<double> _glowAnim;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
    )..repeat(reverse: true);
    _glowAnim = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _pulse, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _glowAnim,
      builder: (context, _) {
        final glow = _glowAnim.value;
        return GestureDetector(
          onTap: widget.onTap,
          child: Container(
            margin: const EdgeInsets.only(bottom: 20),
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color.lerp(const Color(0xFF1E40AF), const Color(0xFF2563EB), glow)!,
                  Color.lerp(const Color(0xFF0EA5E9), const Color(0xFF22D3EE), glow)!,
                ],
              ),
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF2563EB).withValues(alpha: 0.15 + glow * 0.2),
                  blurRadius: 16 + glow * 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Row(
              children: [
                // Icône pulsante
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withValues(alpha: 0.1 + glow * 0.08),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.2 + glow * 0.25),
                      width: 1.5,
                    ),
                  ),
                  child: const Icon(Icons.auto_awesome,
                      color: Colors.white, size: 18),
                ),
                const SizedBox(width: 14),
                // Texte
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Row(
                        children: [
                          const Text(
                            'Création en cours',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w700,
                              fontSize: 13,
                            ),
                          ),
                          const SizedBox(width: 8),
                          _DotsLoader(pulse: _pulse),
                        ],
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${widget.projectName} · ${widget.progressMessage}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.75),
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 10),
                // Bouton voir
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                        color: Colors.white.withValues(alpha: 0.25), width: 1),
                  ),
                  child: const Text(
                    'Voir',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

/// Trois petits points animés pour signaler le chargement
class _DotsLoader extends StatelessWidget {
  const _DotsLoader({required this.pulse});
  final AnimationController pulse;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: pulse,
      builder: (context, _) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (i) {
            final delay = i / 3.0;
            final t = ((pulse.value - delay) % 1.0).abs();
            final opacity = (t < 0.5 ? t * 2 : (1 - t) * 2).clamp(0.3, 1.0);
            return Padding(
              padding: const EdgeInsets.only(right: 2),
              child: Opacity(
                opacity: opacity,
                child: Container(
                  width: 4,
                  height: 4,
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            );
          }),
        );
      },
    );
  }
}
