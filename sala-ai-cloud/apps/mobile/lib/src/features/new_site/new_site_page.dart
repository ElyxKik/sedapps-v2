import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../../widgets/page_scaffold.dart';
import '../agents/agent_state.dart';

class NewSitePage extends ConsumerStatefulWidget {
  const NewSitePage({super.key});

  @override
  ConsumerState<NewSitePage> createState() => _NewSitePageState();
}

class _NewSitePageState extends ConsumerState<NewSitePage> {
  final _business = TextEditingController();
  final _sector = TextEditingController();
  final _brief = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _business.dispose();
    _sector.dispose();
    _brief.dispose();
    super.dispose();
  }

  Future<void> _generate() async {
    if (_business.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Le nom du business est requis')));
      return;
    }
    setState(() => _loading = true);
    try {
      final api = ref.read(apiClientProvider);
      final project = await api.createProject(_business.text.trim(),
          _sector.text.trim().isEmpty ? null : _sector.text.trim());
      await api.saveOnboarding(project['id'].toString(), {
        'business_name': _business.text.trim(),
        'sector': _sector.text.trim(),
        'brief': _brief.text.trim(),
      });
      final job = await api.generateSite(project['id'].toString());
      final jobId = job['job_id']?.toString() ?? job['id']?.toString();
      ref.read(currentJobIdProvider.notifier).state = jobId;
      if (!mounted) return;
      context.go('/projects/${project['id']}');
    } catch (_) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('La génération n\'a pas pu démarrer. Vérifie ta connexion et réessaie.')));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return PageScaffold(
      title: 'Créer un nouveau site',
      subtitle: 'Décris ton projet, nos agents IA vont livrer un site complet',
      action: OutlinedButton.icon(
        onPressed: () => context.go('/projects'),
        icon: const Icon(Icons.close, size: 18),
        label: const Text('Annuler'),
      ),
      children: [
        LayoutBuilder(
          builder: (context, constraints) {
            final wide = constraints.maxWidth > 900;
            final form = _FormSection(
              business: _business,
              sector: _sector,
              brief: _brief,
              loading: _loading,
              onGenerate: _generate,
            );
            final agents = const _AgentsSection();

            if (!wide) {
              return Column(
                  children: [form, const SizedBox(height: 20), agents]);
            }
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(flex: 2, child: form),
                const SizedBox(width: 20),
                Expanded(flex: 1, child: agents),
              ],
            );
          },
        ),
      ],
    );
  }
}

class _FormSection extends StatelessWidget {
  const _FormSection({
    required this.business,
    required this.sector,
    required this.brief,
    required this.loading,
    required this.onGenerate,
  });

  final TextEditingController business;
  final TextEditingController sector;
  final TextEditingController brief;
  final bool loading;
  final VoidCallback onGenerate;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Créons ton site',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            const Text('Réponds à quelques questions. Sala AI prépare une première version adaptée à ton activité.',
                style: TextStyle(color: AppColors.textSecondary)),
            const SizedBox(height: 24),
            Text('Nom de ton activité *',
                style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 6),
            TextField(
              controller: business,
              decoration: const InputDecoration(
                hintText: 'Ex: Maison Léo, Cabinet Martin, Studio Nova',
                prefixIcon: Icon(Icons.business),
              ),
            ),
            const SizedBox(height: 18),
            Text('Secteur d\'activité',
                style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 6),
            TextField(
              controller: sector,
              decoration: const InputDecoration(
                hintText: 'Ex: Restauration, Services numériques, Bien-être...',
                prefixIcon: Icon(Icons.category_outlined),
              ),
            ),
            const SizedBox(height: 18),
            Text('Parle-nous de ton activité',
                style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 6),
            TextField(
              controller: brief,
              maxLines: 6,
              decoration: const InputDecoration(
                hintText:
                    'Explique ce que tu proposes, à qui tu t\'adresses, ce qui te différencie et ce que tu veux que les visiteurs fassent sur ton site.',
                alignLabelWithHint: true,
              ),
            ),
            const SizedBox(height: 24),
            if (loading)
              Column(
                children: const [
                  LinearProgressIndicator(),
                  SizedBox(height: 12),
                  Text(
                      'Sala AI prépare les textes, les pages et le design de ton site.',
                      style: TextStyle(
                          color: AppColors.textSecondary, fontSize: 12)),
                  SizedBox(height: 12),
                ],
              ),
            FilledButton.icon(
              onPressed: loading ? null : onGenerate,
              icon: const Icon(Icons.rocket_launch, size: 18),
              label: Text(
                  loading ? 'Création en cours…' : 'Créer mon site'),
              style: FilledButton.styleFrom(
                padding:
                    const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AgentsSection extends StatelessWidget {
  const _AgentsSection();

  static const _agents = [
    ('Designer', Icons.palette, 'Palette, typo, layout', Color(0xFF0EA5E9)),
    (
      'Copywriter',
      Icons.edit_note,
      'Titres, descriptions, CTA',
      Color(0xFF22D3EE)
    ),
    ('SEO', Icons.search, 'Meta tags, mots-clés', Color(0xFFF59E0B)),
    ('Frontend Dev', Icons.code, 'Composants et code', Color(0xFF10B981)),
  ];

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Les agents IA',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            const Text('Qui vont collaborer sur ton site',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            const SizedBox(height: 20),
            for (var i = 0; i < _agents.length; i++) ...[
              _AgentCard(
                name: _agents[i].$1,
                icon: _agents[i].$2,
                desc: _agents[i].$3,
                color: _agents[i].$4,
              ),
              if (i < _agents.length - 1) const SizedBox(height: 12),
            ],
          ],
        ),
      ),
    );
  }
}

class _AgentCard extends StatelessWidget {
  const _AgentCard(
      {required this.name,
      required this.icon,
      required this.desc,
      required this.color});
  final String name;
  final IconData icon;
  final String desc;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
                color: color, borderRadius: BorderRadius.circular(10)),
            child: Icon(icon, color: Colors.white, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name,
                    style: const TextStyle(
                        fontWeight: FontWeight.w700, fontSize: 13)),
                Text(desc,
                    style: const TextStyle(
                        color: AppColors.textSecondary, fontSize: 11)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
