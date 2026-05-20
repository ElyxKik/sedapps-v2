import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../agents/agent_state.dart';
import '../projects/project_loading_page.dart';

class OnboardingPage extends ConsumerStatefulWidget {
  const OnboardingPage({super.key});

  @override
  ConsumerState<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends ConsumerState<OnboardingPage> {
  final _projectNameController = TextEditingController();
  final _domainController = TextEditingController();
  final _brandNameController = TextEditingController();
  final _taglineController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _contactEmailController = TextEditingController();
  final _briefController = TextEditingController();
  int _step = 1;
  String? _stack = 'onepage';
  String _projectType = 'Personnalisé';
  Color _primaryColor = AppColors.skyBlue;
  Color _secondaryColor = const Color(0xFF8B5CF6);
  String _fontStyle = 'Inter';
  bool _loading = false;

  static const _stacks = [
    _StackOption(
      id: 'onepage',
      label: 'Site One Page',
      desc: 'Une seule page fluide avec sections (hero, services, témoignages, contact). Idéal pour landing, portfolio, lancement produit.',
      icon: Icons.view_agenda_outlined,
      color: Color(0xFF3B82F6),
    ),
    _StackOption(
      id: 'multipage',
      label: 'Site Multipage',
      desc: 'Plusieurs pages reliées (Accueil, À propos, Services, Blog, Contact). Idéal pour entreprises, associations, e-commerce vitrine.',
      icon: Icons.view_quilt_outlined,
      color: Color(0xFF8B5CF6),
    ),
  ];

  static const _projectTypes = [
    'Personnalisé',
    'Portfolio',
    'Boutique e-commerce',
    'ASBL',
    'ONG',
    'Cabinet d\'avocat',
    'Hôpital',
    'Politique',
    'Restaurant',
    'Agence immobilière',
    'Cabinet médical',
    'Salon de beauté',
    'Fitness/Gym',
    'Éducation',
    'Blog',
    'Événements',
  ];

  static const _fonts = [
    'Inter',
    'Plus Jakarta Sans',
    'DM Sans',
    'Poppins',
    'Outfit',
    'Sora',
    'Montserrat',
    'Playfair Display',
    'JetBrains Mono',
  ];

  @override
  void initState() {
    super.initState();
    _projectNameController.addListener(_onProjectNameChanged);
  }

  void _onProjectNameChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _projectNameController.removeListener(_onProjectNameChanged);
    _projectNameController.dispose();
    _domainController.dispose();
    _brandNameController.dispose();
    _taglineController.dispose();
    _descriptionController.dispose();
    _contactEmailController.dispose();
    _briefController.dispose();
    super.dispose();
  }

  String get _projectName => _projectNameController.text.trim().isEmpty ? 'Nouveau site' : _projectNameController.text.trim();

  String get _domain {
    final customDomain = _domainController.text.trim();
    if (customDomain.isNotEmpty) return customDomain;
    final slug = _projectName.toLowerCase().replaceAll(RegExp(r'[^a-z0-9]+'), '-').replaceAll(RegExp(r'^-|-$'), '');
    return '$slug.sedapps.ai';
  }

  _StackOption get _selectedStack => _stacks.firstWhere((stack) => stack.id == _stack, orElse: () => _stacks.first);

  Future<void> _generate() async {
    setState(() => _loading = true);
    try {
      final project = await ref.read(apiClientProvider).createProject(
        _projectName,
        _projectType,
      );
      final projectId = project['id'].toString();
      await ref.read(apiClientProvider).saveOnboarding(projectId, {
        'business_name': _brandNameController.text.trim().isEmpty ? _projectName : _brandNameController.text.trim(),
        'sector': _projectType,
        'brief': _briefController.text.trim(),
        'domain': _domain,
        'stack': _stack,
        'tagline': _taglineController.text.trim(),
        'description': _descriptionController.text.trim(),
        'contact_email': _contactEmailController.text.trim(),
        'primary_color': '#${_primaryColor.value.toRadixString(16).substring(2).toUpperCase()}',
        'secondary_color': '#${_secondaryColor.value.toRadixString(16).substring(2).toUpperCase()}',
        'font_style': _fontStyle,
      });
      final job = await ref.read(apiClientProvider).generateSite(projectId);
      final jobId = job['job_id']?.toString() ?? job['id']?.toString();
      ref.read(currentJobIdProvider.notifier).state = jobId;
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Génération lancée. Les agents apparaissent dans la timeline.')));
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (context) => ProjectLoadingPage(
            projectId: projectId,
            projectName: _projectName,
          ),
        ),
      );
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur génération: $error')));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  double _scale(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    if (width >= 720) return 1.0;
    if (width <= 320) return 0.78;
    return (0.78 + (width - 320) * (0.22 / 400)).clamp(0.78, 1.0);
  }

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final outerPadding = width < 380 ? 14.0 : width < 560 ? 18.0 : 24.0;
    return Scaffold(
      backgroundColor: const Color(0xFF020617),
      body: SafeArea(
        child: Stack(
          children: [
            const Positioned(top: -120, left: -80, child: _Glow(color: Color(0xFF2563EB))),
            const Positioned(bottom: -140, right: -80, child: _Glow(color: Color(0xFF7C3AED))),
            Center(
              child: SingleChildScrollView(
                padding: EdgeInsets.all(outerPadding),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 720),
                  child: Column(
                    children: [
                      _Progress(step: _step, scale: _scale(context)),
                      SizedBox(height: 22 * _scale(context)),
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 280),
                        transitionBuilder: (child, animation) => FadeTransition(
                          opacity: animation,
                          child: SlideTransition(
                            position: Tween<Offset>(begin: const Offset(0.04, 0), end: Offset.zero).animate(animation),
                            child: child,
                          ),
                        ),
                        child: _stepContent(),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _stepContent() {
    final scale = _scale(context);
    return switch (_step) {
      1 => _stepWelcome(scale),
      2 => _stepProjectName(scale),
      3 => _stepBrandContext(scale),
      _ => _stepConfirmation(scale),
    };
  }

  Widget _stepWelcome(double scale) {
    return _GlassPanel(
      key: const ValueKey('step1'),
      scale: scale,
      child: Column(
        children: [
          Container(
            width: 76 * scale,
            height: 76 * scale,
            decoration: BoxDecoration(
              gradient: AppColors.heroGradient,
              borderRadius: BorderRadius.circular(24 * scale),
              boxShadow: [BoxShadow(color: AppColors.skyBlue.withValues(alpha: 0.35), blurRadius: 28, offset: const Offset(0, 12))],
            ),
            child: Icon(Icons.auto_awesome, color: Colors.white, size: 36 * scale),
          ),
          SizedBox(height: 24 * scale),
          Text('Bienvenue dans SedApps 👋', style: TextStyle(color: Colors.white, fontSize: 34 * scale, fontWeight: FontWeight.w800), textAlign: TextAlign.center),
          SizedBox(height: 10 * scale),
          Text(
            'Crée, héberge et gère ton site web en quelques minutes avec un assistant IA professionnel.',
            style: TextStyle(color: Colors.white.withValues(alpha: 0.62), fontSize: 16 * scale, height: 1.5),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: 30 * scale),
          Text('Quel type de projet veux-tu créer ?', style: TextStyle(color: Colors.white, fontSize: 18 * scale, fontWeight: FontWeight.w700), textAlign: TextAlign.center),
          SizedBox(height: 16 * scale),
          LayoutBuilder(
            builder: (context, constraints) {
              final compact = constraints.maxWidth < 560;
              return Wrap(
                spacing: 14,
                runSpacing: 14,
                children: _stacks.map((stack) {
                  final selected = _stack == stack.id;
                  return SizedBox(
                    width: compact ? constraints.maxWidth : (constraints.maxWidth - 14) / 2,
                    child: _StackCard(
                      stack: stack,
                      selected: selected,
                      onTap: () => setState(() => _stack = stack.id),
                    ),
                  );
                }).toList(),
              );
            },
          ),
          const SizedBox(height: 28),
          FilledButton.icon(
            onPressed: _stack == null ? null : () => setState(() => _step = 2),
            icon: const Icon(Icons.arrow_forward),
            label: const Text('Continuer'),
          ),
        ],
      ),
    );
  }

  Widget _stepProjectName(double scale) {
    return _GlassPanel(
      key: const ValueKey('step2'),
      scale: scale,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _Header(icon: _selectedStack.icon, title: 'Nomme ton projet', subtitle: _selectedStack.label, color: _selectedStack.color, scale: scale),
          SizedBox(height: 24 * scale),
          TextField(
            controller: _projectNameController,
            style: TextStyle(color: Colors.white, fontSize: 16 * scale),
            decoration: _darkInput('Nom du projet *', 'Mon super site', Icons.code),
            onSubmitted: (_) {
              if (_projectNameController.text.trim().isNotEmpty) setState(() => _step = 3);
            },
          ),
          SizedBox(height: 16 * scale),
          TextField(
            controller: _domainController,
            style: TextStyle(color: Colors.white, fontSize: 16 * scale),
            decoration: _darkInput('Domaine (optionnel)', 'monsite.fr', Icons.language),
          ),
          SizedBox(height: 8 * scale),
          Text('Laisse vide pour utiliser $_domain', style: TextStyle(color: Colors.white.withValues(alpha: 0.36), fontSize: 12 * scale)),
          SizedBox(height: 24 * scale),
          _Actions(
            back: () => setState(() => _step = 1),
            next: _projectNameController.text.trim().isEmpty ? null : () => setState(() => _step = 3),
            nextLabel: 'Continuer',
          ),
        ],
      ),
    );
  }

  Widget _stepBrandContext(double scale) {
    final width = MediaQuery.sizeOf(context).width;
    final stacked = width < 520;
    return _GlassPanel(
      key: const ValueKey('step3'),
      scale: scale,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _Header(icon: Icons.auto_awesome, title: 'Contexte de marque', subtitle: 'Facultatif — l’IA utilisera ces infos dans chaque génération', color: const Color(0xFF8B5CF6), scale: scale),
          SizedBox(height: 24 * scale),
          TextField(controller: _contactEmailController, style: TextStyle(color: Colors.white, fontSize: 16 * scale), decoration: _darkInput('Email de réception des formulaires', 'contact@monsite.com', Icons.mail_outline)),
          SizedBox(height: 14 * scale),
          _DarkDropdown(value: _projectType, values: _projectTypes, label: 'Type de projet', onChanged: (value) => setState(() => _projectType = value)),
          SizedBox(height: 14 * scale),
          if (stacked)
            Column(
              children: [
                TextField(controller: _brandNameController, style: TextStyle(color: Colors.white, fontSize: 16 * scale), decoration: _darkInput('Nom de la marque', _projectName, Icons.storefront)),
                SizedBox(height: 12 * scale),
                TextField(controller: _taglineController, style: TextStyle(color: Colors.white, fontSize: 16 * scale), decoration: _darkInput('Slogan', 'Just do it', Icons.short_text)),
              ],
            )
          else
            Row(
              children: [
                Expanded(child: TextField(controller: _brandNameController, style: TextStyle(color: Colors.white, fontSize: 16 * scale), decoration: _darkInput('Nom de la marque', _projectName, Icons.storefront))),
                const SizedBox(width: 12),
                Expanded(child: TextField(controller: _taglineController, style: TextStyle(color: Colors.white, fontSize: 16 * scale), decoration: _darkInput('Slogan', 'Just do it', Icons.short_text))),
              ],
            ),
          SizedBox(height: 14 * scale),
          TextField(
            controller: _descriptionController,
            maxLines: 3,
            style: TextStyle(color: Colors.white, fontSize: 16 * scale),
            decoration: _darkInput('Description de l’activité', 'Ex : Boutique de bijoux artisanaux pour femmes 25-45 ans', Icons.description_outlined),
          ),
          SizedBox(height: 14 * scale),
          TextField(
            controller: _briefController,
            maxLines: 3,
            style: TextStyle(color: Colors.white, fontSize: 16 * scale),
            decoration: _darkInput('Brief IA complémentaire', 'Objectifs, cible, ton, offres, pages souhaitées...', Icons.psychology_outlined),
          ),
          SizedBox(height: 18 * scale),
          _ColorPickers(
            primaryColor: _primaryColor,
            secondaryColor: _secondaryColor,
            onPrimaryChanged: (color) => setState(() => _primaryColor = color),
            onSecondaryChanged: (color) => setState(() => _secondaryColor = color),
          ),
          SizedBox(height: 14 * scale),
          _DarkDropdown(value: _fontStyle, values: _fonts, label: 'Police de caractères', onChanged: (value) => setState(() => _fontStyle = value)),
          SizedBox(height: 24 * scale),
          _Actions(back: () => setState(() => _step = 2), next: () => setState(() => _step = 4), nextLabel: 'Continuer'),
        ],
      ),
    );
  }

  Widget _stepConfirmation(double scale) {
    return _GlassPanel(
      key: const ValueKey('step4'),
      scale: scale,
      child: Column(
        children: [
          Container(
            width: 68 * scale,
            height: 68 * scale,
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFF22C55E), Color(0xFF10B981)]),
              borderRadius: BorderRadius.circular(22 * scale),
            ),
            child: Icon(Icons.check_circle, color: Colors.white, size: 36 * scale),
          ),
          SizedBox(height: 20 * scale),
          Text('Tout est prêt !', style: TextStyle(color: Colors.white, fontSize: 28 * scale, fontWeight: FontWeight.w800), textAlign: TextAlign.center),
          SizedBox(height: 8 * scale),
          Text('Voici le résumé de ton projet avant génération.', style: TextStyle(color: Colors.white.withValues(alpha: 0.56), fontSize: 14 * scale), textAlign: TextAlign.center),
          SizedBox(height: 26 * scale),
          _SummaryRow(label: 'Nom', value: _projectName),
          _SummaryRow(label: 'Type', value: _selectedStack.label),
          _SummaryRow(label: 'Catégorie', value: _projectType),
          _SummaryRow(label: 'Domaine', value: _domain, accent: true),
          if (_loading) const Padding(padding: EdgeInsets.only(top: 18), child: LinearProgressIndicator()),
          const SizedBox(height: 24),
          _ResponsiveActions(
            back: _loading ? null : () => setState(() => _step = 3),
            next: _loading ? null : _generate,
            backLabel: 'Modifier',
            nextLabel: _loading ? 'Création en cours…' : 'Ouvrir le Builder',
            nextIcon: _loading ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.rocket_launch),
          ),
        ],
      ),
    );
  }

  InputDecoration _darkInput(String label, String hint, IconData icon) {
    return InputDecoration(
      labelText: label,
      hintText: hint,
      prefixIcon: Icon(icon, color: Colors.white.withValues(alpha: 0.38)),
      labelStyle: TextStyle(color: Colors.white.withValues(alpha: 0.62)),
      hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.28)),
      filled: true,
      fillColor: Colors.white.withValues(alpha: 0.06),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.10))),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: AppColors.skyBlue, width: 1.6)),
    );
  }
}

class _StackOption {
  const _StackOption({required this.id, required this.label, required this.desc, required this.icon, required this.color});
  final String id;
  final String label;
  final String desc;
  final IconData icon;
  final Color color;
}

class _Glow extends StatelessWidget {
  const _Glow({required this.color});
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 260,
      height: 260,
      decoration: BoxDecoration(shape: BoxShape.circle, color: color.withValues(alpha: 0.28), boxShadow: [BoxShadow(color: color.withValues(alpha: 0.35), blurRadius: 120, spreadRadius: 40)]),
    );
  }
}

class _GlassPanel extends StatelessWidget {
  const _GlassPanel({required this.child, this.scale = 1.0, super.key});
  final Widget child;
  final double scale;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(28 * scale),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(30 * scale),
        border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.28), blurRadius: 36, offset: const Offset(0, 18))],
      ),
      child: child,
    );
  }
}

class _Progress extends StatelessWidget {
  const _Progress({required this.step, this.scale = 1.0});
  final int step;
  final double scale;

  @override
  Widget build(BuildContext context) {
    final size = 34 * scale;
    final connector = 42 * scale;
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(4, (index) {
        final item = index + 1;
        final done = item < step;
        final active = item == step;
        return Row(
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 220),
              width: size,
              height: size,
              decoration: BoxDecoration(
                color: done ? AppColors.skyBlue : active ? AppColors.skyBlue.withValues(alpha: 0.18) : Colors.white.withValues(alpha: 0.06),
                border: Border.all(color: done || active ? AppColors.skyBlue : Colors.white.withValues(alpha: 0.16), width: active ? 2 : 1),
                shape: BoxShape.circle,
              ),
              child: Center(
                child: done
                    ? Icon(Icons.check, color: Colors.white, size: 18 * scale)
                    : Text('$item', style: TextStyle(color: active ? AppColors.skyBlueAccent : Colors.white.withValues(alpha: 0.42), fontWeight: FontWeight.w800, fontSize: 14 * scale)),
              ),
            ),
            if (item < 4)
              AnimatedContainer(
                duration: const Duration(milliseconds: 220),
                width: connector,
                height: 2,
                margin: EdgeInsets.symmetric(horizontal: 8 * scale),
                color: item < step ? AppColors.skyBlue : Colors.white.withValues(alpha: 0.12),
              ),
          ],
        );
      }),
    );
  }
}

class _StackCard extends StatelessWidget {
  const _StackCard({required this.stack, required this.selected, required this.onTap});
  final _StackOption stack;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: selected ? stack.color.withValues(alpha: 0.20) : Colors.white.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: selected ? stack.color : Colors.white.withValues(alpha: 0.12), width: selected ? 2 : 1),
        ),
        child: Stack(
          children: [
            if (selected) const Positioned(right: 0, top: 0, child: Icon(Icons.check_circle, color: Colors.white, size: 22)),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(color: stack.color, borderRadius: BorderRadius.circular(14)),
                  child: Icon(stack.icon, color: Colors.white),
                ),
                const SizedBox(height: 14),
                Text(stack.label, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w800)),
                const SizedBox(height: 5),
                Text(stack.desc, style: TextStyle(color: Colors.white.withValues(alpha: 0.50), fontSize: 12, height: 1.35)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.icon, required this.title, required this.subtitle, required this.color, this.scale = 1.0});
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final double scale;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 46 * scale,
          height: 46 * scale,
          decoration: BoxDecoration(color: color.withValues(alpha: 0.22), borderRadius: BorderRadius.circular(15 * scale)),
          child: Icon(icon, color: color, size: 24 * scale),
        ),
        SizedBox(width: 14 * scale),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: TextStyle(color: Colors.white, fontSize: 22 * scale, fontWeight: FontWeight.w800)),
              SizedBox(height: 3 * scale),
              Text(subtitle, style: TextStyle(color: Colors.white.withValues(alpha: 0.45), fontSize: 13 * scale)),
            ],
          ),
        ),
      ],
    );
  }
}

class _Actions extends StatelessWidget {
  const _Actions({required this.back, required this.next, required this.nextLabel});
  final VoidCallback back;
  final VoidCallback? next;
  final String nextLabel;

  @override
  Widget build(BuildContext context) {
    return _ResponsiveActions(back: back, next: next, backLabel: 'Retour', nextLabel: nextLabel);
  }
}

class _ResponsiveActions extends StatelessWidget {
  const _ResponsiveActions({
    required this.back,
    required this.next,
    required this.backLabel,
    required this.nextLabel,
    this.nextIcon = const Icon(Icons.arrow_forward),
  });

  final VoidCallback? back;
  final VoidCallback? next;
  final String backLabel;
  final String nextLabel;
  final Widget nextIcon;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final stacked = constraints.maxWidth < 360;
        final backButton = OutlinedButton.icon(
          onPressed: back,
          icon: const Icon(Icons.arrow_back),
          label: Text(backLabel, overflow: TextOverflow.ellipsis),
        );
        final nextButton = FilledButton.icon(
          onPressed: next,
          icon: nextIcon,
          label: Text(nextLabel, overflow: TextOverflow.ellipsis),
        );
        if (stacked) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              nextButton,
              const SizedBox(height: 10),
              backButton,
            ],
          );
        }
        return Row(
          children: [
            Flexible(child: backButton),
            const SizedBox(width: 12),
            Expanded(flex: 2, child: nextButton),
          ],
        );
      },
    );
  }
}

class _DarkDropdown extends StatelessWidget {
  const _DarkDropdown({required this.value, required this.values, required this.label, required this.onChanged});
  final String value;
  final List<String> values;
  final String label;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<String>(
      value: value,
      dropdownColor: const Color(0xFF0F172A),
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: TextStyle(color: Colors.white.withValues(alpha: 0.62)),
        filled: true,
        fillColor: Colors.white.withValues(alpha: 0.06),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.10))),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: AppColors.skyBlue, width: 1.6)),
      ),
      items: values.map((value) => DropdownMenuItem(value: value, child: Text(value))).toList(),
      onChanged: (value) {
        if (value != null) onChanged(value);
      },
    );
  }
}

class _ColorPickers extends StatelessWidget {
  const _ColorPickers({required this.primaryColor, required this.secondaryColor, required this.onPrimaryChanged, required this.onSecondaryChanged});
  final Color primaryColor;
  final Color secondaryColor;
  final ValueChanged<Color> onPrimaryChanged;
  final ValueChanged<Color> onSecondaryChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(child: _ColorChoice(label: 'Principale', color: primaryColor, options: const [AppColors.skyBlue, Color(0xFF3B82F6), Color(0xFF22C55E), Color(0xFFEF4444)], onChanged: onPrimaryChanged)),
        const SizedBox(width: 12),
        Expanded(child: _ColorChoice(label: 'Secondaire', color: secondaryColor, options: const [Color(0xFF8B5CF6), Color(0xFF38BDF8), Color(0xFFF59E0B), Color(0xFFEC4899)], onChanged: onSecondaryChanged)),
      ],
    );
  }
}

class _ColorChoice extends StatelessWidget {
  const _ColorChoice({required this.label, required this.color, required this.options, required this.onChanged});
  final String label;
  final Color color;
  final List<Color> options;
  final ValueChanged<Color> onChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.06), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white.withValues(alpha: 0.10))),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.58), fontSize: 12)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            children: options.map((option) {
              final selected = option.value == color.value;
              return InkWell(
                onTap: () => onChanged(option),
                borderRadius: BorderRadius.circular(99),
                child: Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(color: option, shape: BoxShape.circle, border: Border.all(color: selected ? Colors.white : Colors.transparent, width: 3)),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

class _SummaryRow extends StatelessWidget {
  const _SummaryRow({required this.label, required this.value, this.accent = false});
  final String label;
  final String value;
  final bool accent;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.06), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white.withValues(alpha: 0.10))),
      child: Row(
        children: [
          Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.48))),
          const Spacer(),
          Flexible(child: Text(value, textAlign: TextAlign.right, style: TextStyle(color: accent ? AppColors.skyBlueAccent : Colors.white, fontWeight: FontWeight.w700))),
        ],
      ),
    );
  }
}
