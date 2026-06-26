import 'dart:convert';
import 'dart:html' as html;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_colorpicker/flutter_colorpicker.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';
import '../agents/agent_state.dart';
import '../projects/project_loading_page.dart';
import '../../widgets/active_job_banner.dart';

// ────────────────────────────────────────────────────────────────────────────
// Data models
// ────────────────────────────────────────────────────────────────────────────

class _SectionConfig {
  final String type;
  final String label;
  final IconData icon;
  final Color color;
  bool enabled;
  Map<String, dynamic> data;

  _SectionConfig({
    required this.type,
    required this.label,
    required this.icon,
    required this.color,
    this.enabled = false,
    Map<String, dynamic>? data,
  }) : data = data ?? {};

  Map<String, dynamic> toJson() => {'type': type, 'enabled': enabled, 'data': data};
}

class _StackOption {
  const _StackOption({
    required this.id,
    required this.label,
    required this.desc,
    required this.icon,
    required this.color,
  });
  final String id;
  final String label;
  final String desc;
  final IconData icon;
  final Color color;
}

class _FontOption {
  const _FontOption(this.label, this.category);
  final String label;
  final String category;
}

// ────────────────────────────────────────────────────────────────────────────
// Page
// ────────────────────────────────────────────────────────────────────────────

class OnboardingPage extends ConsumerStatefulWidget {
  const OnboardingPage({super.key});

  @override
  ConsumerState<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends ConsumerState<OnboardingPage> {
  // Step 1 — Site type
  String _stack = 'onepage';
  bool _premium = false;
  String _projectType = 'Personnalisé';

  // Step 2 — Project name & domain
  final _projectNameController = TextEditingController();
  final _domainController = TextEditingController();

  // Step 3 — Brand identity
  final _brandNameController = TextEditingController();
  final _taglineController = TextEditingController();
  final _descriptionController = TextEditingController();
  Color _primaryColor = AppColors.skyBlue;
  Color _secondaryColor = const Color(0xFF0EA5E9);
  String _fontStyle = 'Inter';
  String _tone = 'professionnel';
  final Set<String> _styleKeywords = {};
  String? _logoBase64;
  String? _logoFileName;

  // Step 4 — Sections
  late List<_SectionConfig> _sections;

  // Step 5 — Contact & details
  final _contactEmailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _addressController = TextEditingController();
  final _instagramController = TextEditingController();
  final _facebookController = TextEditingController();
  final _linkedinController = TextEditingController();
  final _objectivesController = TextEditingController();
  final _targetAudienceController = TextEditingController();
  final Set<String> _selectedPages = {'home', 'about', 'services', 'contact'};

  int _step = 1;
  bool _loading = false;

  // ── Static data ─────────────────────────────────────────────────────────

  static const _stacks = [
    _StackOption(
      id: 'onepage',
      label: 'Site simple',
      desc: 'Une seule page claire avec toutes les informations essentielles. Idéal pour présenter rapidement ton activité.',
      icon: Icons.view_agenda_outlined,
      color: Color(0xFF3B82F6),
    ),
    _StackOption(
      id: 'multipage',
      label: 'Site complet',
      desc: 'Plusieurs pages pour détailler tes services, ton histoire, tes réalisations et tes contacts.',
      icon: Icons.view_quilt_outlined,
      color: Color(0xFF0EA5E9),
    ),
  ];

  static const _sectors = [
    ('Autre activité', Icons.tune),
    ('Restaurant / Café / Bar', Icons.restaurant),
    ('Cabinet médical / Kiné', Icons.local_hospital),
    ('Boutique en ligne', Icons.shopping_bag),
    ('Portfolio ou agence', Icons.brush),
    ('Fitness / Sport / Bien-être', Icons.fitness_center),
    ('Avocat, notaire ou juridique', Icons.gavel),
    ('Immobilier', Icons.home_work),
    ('Hôtel / Gîte / Location', Icons.hotel),
    ('Blog / Magazine', Icons.article),
    ('ASBL / ONG / Association', Icons.volunteer_activism),
    ('Formation / Coaching', Icons.school),
    ('Artisan ou bâtiment', Icons.construction),
    ('Technologie ou startup', Icons.code),
    ('Événements', Icons.event),
  ];

  static const _tones = [
    ('professionnel', 'Professionnel'),
    ('chaleureux', 'Chaleureux'),
    ('créatif', 'Créatif'),
    ('luxe', 'Haut de gamme'),
    ('minimaliste', 'Minimaliste'),
    ('dynamique', 'Dynamique'),
    ('sérieux', 'Sérieux'),
    ('décontracté', 'Décontracté'),
  ];

  static const _styleKeywordOptions = [
    'moderne', 'élégant', 'audacieux', 'épuré', 'coloré',
    'sombre', 'lumineux', 'naturel', 'technologique', 'artisanal',
    'premium', 'accessible', 'ludique', 'corporate', 'vintage',
  ];

  static const _availablePages = [
    'home', 'about', 'services', 'portfolio',
    'blog', 'contact', 'faq', 'pricing',
    'team', 'testimonials', 'gallery', 'booking',
  ];

  static const _fonts = [
    _FontOption('Inter', 'Sans-serif moderne'),
    _FontOption('Plus Jakarta Sans', 'Sans-serif moderne'),
    _FontOption('DM Sans', 'Sans-serif moderne'),
    _FontOption('Nunito', 'Sans-serif arrondi'),
    _FontOption('Poppins', 'Sans-serif géométrique'),
    _FontOption('Outfit', 'Sans-serif géométrique'),
    _FontOption('Sora', 'Sans-serif tech'),
    _FontOption('Space Grotesk', 'Sans-serif tech'),
    _FontOption('Geist', 'Sans-serif minimaliste'),
    _FontOption('Raleway', 'Sans-serif élégant'),
    _FontOption('Montserrat', 'Sans-serif premium'),
    _FontOption('Lato', 'Sans-serif classique'),
    _FontOption('Playfair Display', 'Serif élégant'),
    _FontOption('Merriweather', 'Serif lisible'),
    _FontOption('Lora', 'Serif littéraire'),
    _FontOption('Cormorant Garamond', 'Serif luxe'),
    _FontOption('DM Serif Display', 'Serif display'),
    _FontOption('JetBrains Mono', 'Monospace'),
    _FontOption('Bebas Neue', 'Display bold'),
    _FontOption('Oswald', 'Display condensé'),
  ];

  // ── Section catalogue ────────────────────────────────────────────────────

  List<_SectionConfig> _buildSectionCatalogue(String sector) {
    final all = [
      _SectionConfig(type: 'hero', label: 'Hero / Bannière principale', icon: Icons.web_asset, color: const Color(0xFF3B82F6), enabled: true, data: {'headline': '', 'subheadline': '', 'cta_primary': 'Nous contacter', 'cta_secondary': 'En savoir plus', 'background_type': 'gradient'}),
      _SectionConfig(type: 'services', label: 'Services / Offres', icon: Icons.grid_view, color: const Color(0xFF0EA5E9), enabled: true, data: {'title': 'Nos services', 'items': <Map<String, String>>[]}),
      _SectionConfig(type: 'about', label: 'À propos / Notre histoire', icon: Icons.info_outline, color: const Color(0xFF06B6D4), enabled: false, data: {'title': 'À propos', 'body': '', 'founder_name': ''}),
      _SectionConfig(type: 'testimonials', label: 'Témoignages clients', icon: Icons.format_quote, color: const Color(0xFF10B981), enabled: false, data: {'items': <Map<String, String>>[]}),
      _SectionConfig(type: 'gallery', label: 'Galerie / Portfolio', icon: Icons.photo_library_outlined, color: const Color(0xFFF59E0B), enabled: false, data: {'title': 'Nos réalisations', 'style': 'grid'}),
      _SectionConfig(type: 'pricing', label: 'Tarifs / Plans', icon: Icons.sell_outlined, color: const Color(0xFF22D3EE), enabled: false, data: {'title': 'Nos tarifs', 'plans': <Map<String, dynamic>>[]}),
      _SectionConfig(type: 'faq', label: 'FAQ', icon: Icons.help_outline, color: const Color(0xFF0EA5E9), enabled: false, data: {'items': <Map<String, String>>[]}),
      _SectionConfig(type: 'contact', label: 'Formulaire de contact', icon: Icons.contact_mail_outlined, color: const Color(0xFF14B8A6), enabled: true, data: {'title': 'Contactez-nous', 'subtitle': 'Réponse sous 24h'}),
      _SectionConfig(type: 'booking', label: 'Réservation en ligne', icon: Icons.calendar_month_outlined, color: const Color(0xFF0EA5E9), enabled: false, data: {'title': 'Réserver', 'booking_url': ''}),
      _SectionConfig(type: 'menu', label: 'Carte / Menu (restaurant)', icon: Icons.menu_book_outlined, color: const Color(0xFFF97316), enabled: false, data: {'title': 'Notre carte', 'items': <Map<String, String>>[]}),
      _SectionConfig(type: 'team', label: 'Équipe / Membres', icon: Icons.people_outline, color: const Color(0xFF22D3EE), enabled: false, data: {'title': 'Notre équipe', 'members': <Map<String, String>>[]}),
      _SectionConfig(type: 'stats', label: 'Chiffres clés / Stats', icon: Icons.bar_chart, color: const Color(0xFF22D3EE), enabled: false, data: {'items': <Map<String, String>>[]}),
      _SectionConfig(type: 'blog', label: 'Blog / Articles récents', icon: Icons.article_outlined, color: const Color(0xFF84CC16), enabled: false, data: {'title': 'Nos articles'}),
      _SectionConfig(type: 'cta_banner', label: 'Bannière d\'appel à l\'action', icon: Icons.campaign_outlined, color: const Color(0xFFEF4444), enabled: false, data: {'title': '', 'cta': 'Commencer maintenant'}),
    ];

    // Pre-enable sections by sector
    final lower = sector.toLowerCase();
    if (lower.contains('restaurant') || lower.contains('café') || lower.contains('bar')) {
      for (final s in all) {
        if (['menu', 'gallery', 'booking', 'testimonials'].contains(s.type)) s.enabled = true;
      }
    } else if (lower.contains('médical') || lower.contains('kiné') || lower.contains('cabinet')) {
      for (final s in all) {
        if (['team', 'booking', 'faq', 'about'].contains(s.type)) s.enabled = true;
      }
    } else if (lower.contains('portfolio') || lower.contains('agence')) {
      for (final s in all) {
        if (['gallery', 'testimonials', 'pricing', 'about'].contains(s.type)) s.enabled = true;
      }
    } else if (lower.contains('e-commerce') || lower.contains('boutique')) {
      for (final s in all) {
        if (['gallery', 'testimonials', 'faq', 'pricing'].contains(s.type)) s.enabled = true;
      }
    } else if (lower.contains('fitness') || lower.contains('sport')) {
      for (final s in all) {
        if (['pricing', 'team', 'testimonials', 'gallery'].contains(s.type)) s.enabled = true;
      }
    }
    return all;
  }

  // ── Lifecycle ─────────────────────────────────────────────────────────────

  @override
  void initState() {
    super.initState();
    _sections = _buildSectionCatalogue(_projectType);
    _projectNameController.addListener(_onProjectNameChanged);
  }

  void _onProjectNameChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _projectNameController.removeListener(_onProjectNameChanged);
    for (final c in [
      _projectNameController, _domainController, _brandNameController,
      _taglineController, _descriptionController, _contactEmailController,
      _phoneController, _addressController, _instagramController,
      _facebookController, _linkedinController, _objectivesController,
      _targetAudienceController,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  // ── Computed ──────────────────────────────────────────────────────────────

  String get _projectName => _projectNameController.text.trim().isEmpty
      ? 'Nouveau site'
      : _projectNameController.text.trim();

  String get _domain {
    final custom = _domainController.text.trim();
    if (custom.isNotEmpty) return custom;
    final slug = _projectName
        .toLowerCase()
        .replaceAll(RegExp(r'[^a-z0-9]+'), '-')
        .replaceAll(RegExp(r'^-|-$'), '');
    return '$slug.sala.ai';
  }

  String _colorHex(Color c) =>
      '#${c.value.toRadixString(16).substring(2).toUpperCase()}';

  // ── Logo picker ───────────────────────────────────────────────────────────

  Future<void> _pickLogo() async {
    try {
      final input = html.FileUploadInputElement()
        ..accept = 'image/png,image/jpeg,image/webp,image/gif,image/svg+xml';
      input.click();
      await input.onChange.first;
      if (input.files != null && input.files!.isNotEmpty) {
        final file = input.files![0];
        final reader = html.FileReader();
        reader.readAsDataUrl(file);
        await reader.onLoad.first;
        setState(() {
          _logoBase64 = reader.result as String;
          _logoFileName = file.name;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Impossible de charger ce fichier. Utilise un PNG, JPG ou SVG.')),
        );
      }
    }
  }

  // ── Generate ──────────────────────────────────────────────────────────────

  Future<void> _generate() async {
    setState(() => _loading = true);
    try {
      final project = await ref.read(apiClientProvider).createProject(
            _projectName,
            _projectType,
          );
      final projectId = project['id'].toString();

      final businessName = _brandNameController.text.trim().isEmpty
          ? _projectName
          : _brandNameController.text.trim();

      // Flat payload matching backend OnboardingIn schema (Pydantic validates
      // required fields business_name & sector at root level).
      final onboardingPayload = <String, dynamic>{
        'business_name': businessName,
        'sector': _projectType,
        'tagline': _taglineController.text.trim(),
        'description': _descriptionController.text.trim(),
        'brief': _descriptionController.text.trim(),
        'domain': _domain,
        'stack': _stack,
        'premium': _premium,
        'contact_email': _contactEmailController.text.trim(),
        'contact_phone': _phoneController.text.trim(),
        'primary_color': _colorHex(_primaryColor),
        'secondary_color': _colorHex(_secondaryColor),
        'font_style': _fontStyle,
        'logo_url': _logoBase64,
        'pages': _stack == 'onepage' ? ['home'] : _selectedPages.toList(),
        'tone': _tone,
        'style_keywords': _styleKeywords.toList(),
        'target_audience': _targetAudienceController.text.trim().isEmpty
            ? null
            : _targetAudienceController.text.trim(),
        'objectives': _objectivesController.text.trim().isEmpty
            ? <String>[]
            : _objectivesController.text.trim().split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList(),
        // Rich nested data stored as extra fields (extra: allow on backend)
        'identity': {
          'business_name': businessName,
          'tagline': _taglineController.text.trim(),
          'description': _descriptionController.text.trim(),
          'logo_url': _logoBase64,
          'sector': _projectType,
          'stack': _stack,
          'premium': _premium,
        },
        'brand': {
          'primary_color': _colorHex(_primaryColor),
          'secondary_color': _colorHex(_secondaryColor),
          'font_heading': _fontStyle,
          'font_body': _fontStyle,
          'tone': _tone,
          'style_keywords': _styleKeywords.toList(),
        },
        'contact': {
          'email': _contactEmailController.text.trim(),
          'phone': _phoneController.text.trim(),
          'address': _addressController.text.trim(),
        },
        'social': {
          'instagram': _instagramController.text.trim(),
          'facebook': _facebookController.text.trim(),
          'linkedin': _linkedinController.text.trim(),
        },
        'sections':
            _sections.where((s) => s.enabled).map((s) => s.toJson()).toList(),
      };

      await ref.read(apiClientProvider).saveOnboarding(projectId, onboardingPayload);
      final job = await ref.read(apiClientProvider).generateSite(projectId);
      final jobId = job['job_id']?.toString() ?? job['id']?.toString();
      ref.read(currentJobIdProvider.notifier).state = jobId;
      ref.read(currentJobProjectIdProvider.notifier).state = projectId;
      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (context) => ProjectLoadingPage(
            projectId: projectId,
            projectName: _projectName,
          ),
        ),
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('La création n\'a pas pu démarrer. Vérifie ta connexion et réessaie.')));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  // ── Layout helpers ────────────────────────────────────────────────────────

  double _scale(BuildContext context) {
    final w = MediaQuery.sizeOf(context).width;
    if (w >= 720) return 1.0;
    if (w <= 320) return 0.78;
    return (0.78 + (w - 320) * (0.22 / 400)).clamp(0.78, 1.0);
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
            const Positioned(bottom: -140, right: -80, child: _Glow(color: Color(0xFF0EA5E9))),
            Center(
              child: SingleChildScrollView(
                padding: EdgeInsets.all(outerPadding),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 720),
                  child: Column(
                    children: [
                      const ActiveJobBanner(),
                      if (ref.watch(currentJobIdProvider) != null) const SizedBox(height: 20),
                      _Progress(step: _step, totalSteps: 5, scale: _scale(context)),
                      SizedBox(height: 22 * _scale(context)),
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 280),
                        transitionBuilder: (child, animation) => FadeTransition(
                          opacity: animation,
                          child: SlideTransition(
                            position: Tween<Offset>(begin: const Offset(0.04, 0), end: Offset.zero)
                                .animate(animation),
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
      1 => _stepSiteType(scale),
      2 => _stepProjectName(scale),
      3 => _stepBrandIdentity(scale),
      4 => _stepSections(scale),
      5 => _stepContactDetails(scale),
      _ => _stepConfirmation(scale),
    };
  }

  // ────────────────────────────────────────────────────────────────────────
  // STEP 1 — Site type + sector
  // ────────────────────────────────────────────────────────────────────────

  Widget _stepSiteType(double scale) {
    return _GlassPanel(
      key: const ValueKey('step1'),
      scale: scale,
      child: Column(
        children: [
          // Logo + title
          Container(
            width: 76 * scale, height: 76 * scale,
            decoration: BoxDecoration(
              gradient: AppColors.heroGradient,
              borderRadius: BorderRadius.circular(24 * scale),
              boxShadow: [BoxShadow(color: AppColors.skyBlue.withValues(alpha: 0.35), blurRadius: 28, offset: const Offset(0, 12))],
            ),
            child: Icon(Icons.auto_awesome, color: Colors.white, size: 36 * scale),
          ),
          SizedBox(height: 20 * scale),
          Text('Crée ton site avec Sala AI',
              style: TextStyle(color: Colors.white, fontSize: 28 * scale, fontWeight: FontWeight.w800),
              textAlign: TextAlign.center),
          SizedBox(height: 8 * scale),
          Text('Décris exactement ton site — l\'IA le génère fidèlement.',
              style: TextStyle(color: Colors.white.withValues(alpha: 0.56), fontSize: 14 * scale),
              textAlign: TextAlign.center),
          SizedBox(height: 28 * scale),

          // Structure cards
          Align(
            alignment: Alignment.centerLeft,
            child: Text('1. Structure du site',
                style: TextStyle(color: Colors.white.withValues(alpha: 0.62), fontSize: 13 * scale, fontWeight: FontWeight.w700)),
          ),
          SizedBox(height: 10 * scale),
          LayoutBuilder(builder: (context, constraints) {
            final compact = constraints.maxWidth < 500;
            return Wrap(
              spacing: 12, runSpacing: 12,
              children: _stacks.map((stack) {
                final selected = _stack == stack.id && !_premium;
                return SizedBox(
                  width: compact ? constraints.maxWidth : (constraints.maxWidth - 12) / 2,
                  child: _StackCard(
                    stack: stack, selected: selected,
                    onTap: () => setState(() { _stack = stack.id; _premium = false; }),
                  ),
                );
              }).toList(),
            );
          }),
          const SizedBox(height: 12),
          _PremiumCard(
            selected: _premium,
            onTap: () => setState(() => _premium = !_premium),
          ),
          SizedBox(height: 22 * scale),

          // Sector chips
          Align(
            alignment: Alignment.centerLeft,
            child: Text('2. Secteur d\'activité',
                style: TextStyle(color: Colors.white.withValues(alpha: 0.62), fontSize: 13 * scale, fontWeight: FontWeight.w700)),
          ),
          SizedBox(height: 10 * scale),
          Wrap(
            spacing: 8, runSpacing: 8,
            children: _sectors.map((s) {
              final selected = _projectType == s.$1;
              return GestureDetector(
                onTap: () => setState(() {
                  _projectType = s.$1;
                  _sections = _buildSectionCatalogue(s.$1);
                }),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 160),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                  decoration: BoxDecoration(
                    color: selected ? AppColors.skyBlue.withValues(alpha: 0.22) : Colors.white.withValues(alpha: 0.07),
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(
                      color: selected ? AppColors.skyBlue : Colors.white.withValues(alpha: 0.14),
                      width: selected ? 1.5 : 1,
                    ),
                  ),
                  child: Row(mainAxisSize: MainAxisSize.min, children: [
                    Icon(s.$2, size: 14, color: selected ? AppColors.skyBlueAccent : Colors.white.withValues(alpha: 0.55)),
                    const SizedBox(width: 5),
                    Text(s.$1, style: TextStyle(
                      color: selected ? AppColors.skyBlueAccent : Colors.white.withValues(alpha: 0.75),
                      fontSize: 12 * scale,
                      fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                    )),
                  ]),
                ),
              );
            }).toList(),
          ),
          SizedBox(height: 28 * scale),
          FilledButton.icon(
            onPressed: () => setState(() => _step = 2),
            icon: const Icon(Icons.arrow_forward),
            label: const Text('Continuer'),
          ),
        ],
      ),
    );
  }

  // ────────────────────────────────────────────────────────────────────────
  // STEP 2 — Project name + domain
  // ────────────────────────────────────────────────────────────────────────

  Widget _stepProjectName(double scale) {
    return _GlassPanel(
      key: const ValueKey('step2'),
      scale: scale,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _Header(
            icon: Icons.edit_note,
            title: 'Nomme ton site',
            subtitle: _premium ? 'Offre Premium — $_projectType' : '${_stack == 'onepage' ? 'Site simple' : 'Site complet'} — $_projectType',
            color: _premium ? const Color(0xFFF59E0B) : (_stack == 'onepage' ? const Color(0xFF3B82F6) : const Color(0xFF0EA5E9)),
            scale: scale,
          ),
          SizedBox(height: 24 * scale),
          TextField(
            controller: _projectNameController,
            style: TextStyle(color: Colors.white, fontSize: 16 * scale),
            decoration: _darkInput('Nom de ton site *', 'Ex : Boulangerie Martin, Cabinet Vétérinaire...', Icons.edit_outlined),
          ),
          SizedBox(height: 14 * scale),
          TextField(
            controller: _domainController,
            style: TextStyle(color: Colors.white, fontSize: 16 * scale),
            decoration: _darkInput('Adresse personnalisée (optionnel)', 'monsite.fr', Icons.language),
          ),
          SizedBox(height: 6 * scale),
          Text('Adresse automatique : $_domain',
              style: TextStyle(color: Colors.white.withValues(alpha: 0.34), fontSize: 11 * scale)),
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

  // ────────────────────────────────────────────────────────────────────────
  // STEP 3 — Brand identity
  // ────────────────────────────────────────────────────────────────────────

  Widget _stepBrandIdentity(double scale) {
    final stacked = MediaQuery.sizeOf(context).width < 520;
    return _GlassPanel(
      key: const ValueKey('step3'),
      scale: scale,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _Header(icon: Icons.palette_outlined, title: 'Identité de marque', subtitle: 'Couleurs, typo, ton et logo', color: const Color(0xFF0EA5E9), scale: scale),
          SizedBox(height: 24 * scale),

          // Name + tagline
          if (stacked) ...[
            TextField(controller: _brandNameController, style: TextStyle(color: Colors.white, fontSize: 16 * scale),
                decoration: _darkInput('Nom de la marque', _projectName, Icons.storefront)),
            SizedBox(height: 12 * scale),
            TextField(controller: _taglineController, style: TextStyle(color: Colors.white, fontSize: 16 * scale),
                decoration: _darkInput('Slogan', 'Votre promesse en une phrase', Icons.short_text)),
          ] else
            Row(children: [
              Expanded(child: TextField(controller: _brandNameController, style: TextStyle(color: Colors.white, fontSize: 16 * scale),
                  decoration: _darkInput('Nom de la marque', _projectName, Icons.storefront))),
              const SizedBox(width: 12),
              Expanded(child: TextField(controller: _taglineController, style: TextStyle(color: Colors.white, fontSize: 16 * scale),
                  decoration: _darkInput('Slogan', 'Votre promesse', Icons.short_text))),
            ]),
          SizedBox(height: 14 * scale),

          TextField(
            controller: _descriptionController, maxLines: 3,
            style: TextStyle(color: Colors.white, fontSize: 16 * scale),
            decoration: _darkInput('Description de l\'activité', 'Ce que vous faites, pour qui, depuis combien de temps...', Icons.description_outlined),
          ),
          SizedBox(height: 14 * scale),

          // Logo upload
          Text('Logo', style: TextStyle(color: Colors.white.withValues(alpha: 0.62), fontSize: 12)),
          const SizedBox(height: 6),
          InkWell(
            onTap: _pickLogo,
            borderRadius: BorderRadius.circular(16),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 160),
              padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 16),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: _logoBase64 != null ? 0.08 : 0.04),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: _logoBase64 != null ? AppColors.skyBlue.withValues(alpha: 0.5) : Colors.white.withValues(alpha: 0.20)),
              ),
              child: Column(children: [
                if (_logoBase64 != null) ...[
                  Image.memory(base64Decode(_logoBase64!.split(',')[1]), height: 48, fit: BoxFit.contain),
                  const SizedBox(height: 8),
                  Text(_logoFileName ?? 'logo', style: const TextStyle(color: Colors.white, fontSize: 12)),
                  Text('Appuyer pour changer', style: TextStyle(color: Colors.white.withValues(alpha: 0.38), fontSize: 11)),
                ] else ...[
                  Icon(Icons.upload_file, color: Colors.white.withValues(alpha: 0.38), size: 28),
                  const SizedBox(height: 6),
                  Text('Charger un logo (PNG, SVG, JPG)', style: TextStyle(color: Colors.white.withValues(alpha: 0.48), fontSize: 12)),
                ],
              ]),
            ),
          ),
          SizedBox(height: 18 * scale),

          // Colors
          _ColorPickers(
            primaryColor: _primaryColor,
            secondaryColor: _secondaryColor,
            onPrimaryChanged: (c) => setState(() => _primaryColor = c),
            onSecondaryChanged: (c) => setState(() => _secondaryColor = c),
          ),
          SizedBox(height: 14 * scale),

          // Font
          _FontPickerDropdown(
            value: _fontStyle, options: _fonts,
            label: 'Police de caractères',
            onChanged: (v) => setState(() => _fontStyle = v),
          ),
          SizedBox(height: 18 * scale),

          // Tone
          Text('Ton et ambiance', style: TextStyle(color: Colors.white.withValues(alpha: 0.62), fontSize: 12, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8, runSpacing: 8,
            children: _tones.map((t) {
              final sel = _tone == t.$1;
              return GestureDetector(
                onTap: () => setState(() => _tone = t.$1),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 140),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  decoration: BoxDecoration(
                    color: sel ? const Color(0xFF0EA5E9).withValues(alpha: 0.24) : Colors.white.withValues(alpha: 0.06),
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: sel ? const Color(0xFF0EA5E9) : Colors.white.withValues(alpha: 0.12), width: sel ? 1.5 : 1),
                  ),
                  child: Text(t.$2, style: TextStyle(
                    color: sel ? const Color(0xFF7DD3FC) : Colors.white.withValues(alpha: 0.70),
                    fontSize: 12, fontWeight: sel ? FontWeight.w700 : FontWeight.w500,
                  )),
                ),
              );
            }).toList(),
          ),
          SizedBox(height: 14 * scale),

          // Style keywords
          Text('Mots-clés de style (optionnel)', style: TextStyle(color: Colors.white.withValues(alpha: 0.62), fontSize: 12, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8, runSpacing: 8,
            children: _styleKeywordOptions.map((kw) {
              final sel = _styleKeywords.contains(kw);
              return GestureDetector(
                onTap: () => setState(() {
                  if (sel) _styleKeywords.remove(kw); else _styleKeywords.add(kw);
                }),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 140),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: sel ? AppColors.skyBlue.withValues(alpha: 0.18) : Colors.white.withValues(alpha: 0.05),
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: sel ? AppColors.skyBlue : Colors.white.withValues(alpha: 0.10)),
                  ),
                  child: Text(kw, style: TextStyle(
                    color: sel ? AppColors.skyBlueAccent : Colors.white.withValues(alpha: 0.60),
                    fontSize: 11, fontWeight: sel ? FontWeight.w700 : FontWeight.w400,
                  )),
                ),
              );
            }).toList(),
          ),

          SizedBox(height: 24 * scale),
          _Actions(back: () => setState(() => _step = 2), next: () => setState(() => _step = 4), nextLabel: 'Continuer'),
        ],
      ),
    );
  }

  // ────────────────────────────────────────────────────────────────────────
  // STEP 4 — Sections of the site
  // ────────────────────────────────────────────────────────────────────────

  Widget _stepSections(double scale) {
    final enabledCount = _sections.where((s) => s.enabled).length;
    return _GlassPanel(
      key: const ValueKey('step4'),
      scale: scale,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _Header(icon: Icons.view_stream_outlined, title: 'Sections du site', subtitle: '$enabledCount section(s) sélectionnée(s)', color: const Color(0xFF06B6D4), scale: scale),
          SizedBox(height: 8 * scale),
          Text('Sélectionne et configure les sections que tu veux sur ton site.',
              style: TextStyle(color: Colors.white.withValues(alpha: 0.50), fontSize: 12 * scale)),
          SizedBox(height: 20 * scale),
          ..._sections.map((section) => _SectionRow(
            section: section,
            onToggle: (val) => setState(() => section.enabled = val),
            onConfigure: () => _openSectionConfigurator(section),
          )),
          SizedBox(height: 24 * scale),
          _Actions(back: () => setState(() => _step = 3), next: () => setState(() => _step = 5), nextLabel: 'Continuer'),
        ],
      ),
    );
  }

  void _openSectionConfigurator(_SectionConfig section) {
    showDialog(
      context: context,
      builder: (context) => _SectionConfigDialog(
        section: section,
        onSave: (data) {
          setState(() {
            section.data = data;
            section.enabled = true;
          });
        },
      ),
    );
  }

  // ────────────────────────────────────────────────────────────────────────
  // STEP 5 — Contact & details
  // ────────────────────────────────────────────────────────────────────────

  Widget _stepContactDetails(double scale) {
    return _GlassPanel(
      key: const ValueKey('step5'),
      scale: scale,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _Header(icon: Icons.contact_page_outlined, title: 'Coordonnées & détails', subtitle: 'Informations de contact, réseaux sociaux', color: const Color(0xFF14B8A6), scale: scale),
          SizedBox(height: 24 * scale),

          TextField(controller: _contactEmailController, style: TextStyle(color: Colors.white, fontSize: 16 * scale),
              decoration: _darkInput('Email de contact', 'contact@monsite.com', Icons.mail_outline)),
          SizedBox(height: 12 * scale),
          TextField(controller: _phoneController, style: TextStyle(color: Colors.white, fontSize: 16 * scale),
              decoration: _darkInput('Téléphone', '+33 6 00 00 00 00', Icons.phone_outlined)),
          SizedBox(height: 12 * scale),
          TextField(controller: _addressController, style: TextStyle(color: Colors.white, fontSize: 16 * scale),
              decoration: _darkInput('Adresse physique (optionnel)', '12 Rue de la Paix, Paris', Icons.location_on_outlined)),
          SizedBox(height: 18 * scale),

          Text('Réseaux sociaux', style: TextStyle(color: Colors.white.withValues(alpha: 0.62), fontSize: 12, fontWeight: FontWeight.w700)),
          const SizedBox(height: 10),
          TextField(controller: _instagramController, style: TextStyle(color: Colors.white, fontSize: 15 * scale),
              decoration: _darkInput('Instagram', 'https://instagram.com/...', Icons.camera_alt_outlined)),
          SizedBox(height: 10 * scale),
          TextField(controller: _facebookController, style: TextStyle(color: Colors.white, fontSize: 15 * scale),
              decoration: _darkInput('Facebook', 'https://facebook.com/...', Icons.facebook_outlined)),
          SizedBox(height: 10 * scale),
          TextField(controller: _linkedinController, style: TextStyle(color: Colors.white, fontSize: 15 * scale),
              decoration: _darkInput('LinkedIn', 'https://linkedin.com/in/...', Icons.language)),
          SizedBox(height: 18 * scale),

          TextField(controller: _objectivesController, style: TextStyle(color: Colors.white, fontSize: 15 * scale),
              decoration: _darkInput('Objectifs du site', 'Générer des leads, vendre, informer...', Icons.flag_outlined)),
          SizedBox(height: 12 * scale),
          TextField(controller: _targetAudienceController, style: TextStyle(color: Colors.white, fontSize: 15 * scale),
              decoration: _darkInput('Cible / Audience', 'Femmes 25-40 ans, professionnels...', Icons.groups_outlined)),

          if (_stack == 'multipage') ...[
            SizedBox(height: 18 * scale),
            Text('Pages du site', style: TextStyle(color: Colors.white.withValues(alpha: 0.62), fontSize: 12, fontWeight: FontWeight.w700)),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8, runSpacing: 8,
              children: _availablePages.map((p) {
                final sel = _selectedPages.contains(p);
                return GestureDetector(
                  onTap: () => setState(() {
                    if (sel && p != 'home') _selectedPages.remove(p);
                    else _selectedPages.add(p);
                  }),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 140),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                    decoration: BoxDecoration(
                      color: sel ? const Color(0xFF14B8A6).withValues(alpha: 0.20) : Colors.white.withValues(alpha: 0.06),
                      borderRadius: BorderRadius.circular(999),
                      border: Border.all(color: sel ? const Color(0xFF14B8A6) : Colors.white.withValues(alpha: 0.12), width: sel ? 1.5 : 1),
                    ),
                    child: Text(p, style: TextStyle(
                      color: sel ? const Color(0xFF5eead4) : Colors.white.withValues(alpha: 0.65),
                      fontSize: 12, fontWeight: sel ? FontWeight.w700 : FontWeight.w400,
                    )),
                  ),
                );
              }).toList(),
            ),
          ],

          SizedBox(height: 24 * scale),
          _Actions(back: () => setState(() => _step = 4), next: () => setState(() => _step = 6), nextLabel: 'Récapitulatif'),
        ],
      ),
    );
  }

  // ────────────────────────────────────────────────────────────────────────
  // STEP 6 — Confirmation
  // ────────────────────────────────────────────────────────────────────────

  Widget _stepConfirmation(double scale) {
    final enabledSections = _sections.where((s) => s.enabled).map((s) => s.label).toList();
    return _GlassPanel(
      key: const ValueKey('step6'),
      scale: scale,
      child: Column(
        children: [
          Container(
            width: 68 * scale, height: 68 * scale,
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFF22C55E), Color(0xFF10B981)]),
              borderRadius: BorderRadius.circular(22 * scale),
            ),
            child: Icon(Icons.check_circle, color: Colors.white, size: 36 * scale),
          ),
          SizedBox(height: 20 * scale),
          Text('Tout est prêt !', style: TextStyle(color: Colors.white, fontSize: 28 * scale, fontWeight: FontWeight.w800), textAlign: TextAlign.center),
          SizedBox(height: 8 * scale),
          Text('L\'IA va générer ton site selon tes spécifications exactes.', style: TextStyle(color: Colors.white.withValues(alpha: 0.56), fontSize: 14 * scale), textAlign: TextAlign.center),
          SizedBox(height: 26 * scale),
          _SummaryRow(label: 'Projet', value: _projectName),
          _SummaryRow(label: 'Mode', value: _premium ? 'Premium 10K' : (_stack == 'onepage' ? 'One Page' : 'Multi Page')),
          _SummaryRow(label: 'Secteur', value: _projectType),
          _SummaryRow(label: 'Ton', value: _tone),
          _SummaryRow(label: 'Domaine', value: _domain, accent: true),
          _SummaryRow(label: 'Sections', value: enabledSections.isEmpty ? 'Aucune' : '${enabledSections.length} section(s)'),
          if (_styleKeywords.isNotEmpty)
            _SummaryRow(label: 'Style', value: _styleKeywords.join(', ')),
          if (_loading)
            const Padding(padding: EdgeInsets.only(top: 18), child: LinearProgressIndicator()),
          const SizedBox(height: 24),
          _ResponsiveActions(
            back: _loading ? null : () => setState(() => _step = 5),
            next: _loading ? null : _generate,
            backLabel: 'Modifier',
            nextLabel: _loading ? 'Génération en cours…' : 'Lancer la génération',
            nextIcon: _loading
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.rocket_launch),
          ),
        ],
      ),
    );
  }

  // ── Input decoration helper ───────────────────────────────────────────────

  InputDecoration _darkInput(String label, String hint, IconData icon) {
    return InputDecoration(
      labelText: label, hintText: hint,
      prefixIcon: Icon(icon, color: Colors.white.withValues(alpha: 0.38)),
      labelStyle: TextStyle(color: Colors.white.withValues(alpha: 0.62)),
      hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.28)),
      filled: true, fillColor: Colors.white.withValues(alpha: 0.06),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.10))),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: AppColors.skyBlue, width: 1.6)),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Section Row
// ────────────────────────────────────────────────────────────────────────────

class _SectionRow extends StatelessWidget {
  const _SectionRow({required this.section, required this.onToggle, required this.onConfigure});
  final _SectionConfig section;
  final ValueChanged<bool> onToggle;
  final VoidCallback onConfigure;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        decoration: BoxDecoration(
          color: section.enabled ? section.color.withValues(alpha: 0.10) : Colors.white.withValues(alpha: 0.04),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: section.enabled ? section.color.withValues(alpha: 0.40) : Colors.white.withValues(alpha: 0.09)),
        ),
        child: ListTile(
          leading: Container(
            width: 38, height: 38,
            decoration: BoxDecoration(
              color: section.color.withValues(alpha: section.enabled ? 0.22 : 0.08),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(section.icon, color: section.enabled ? section.color : Colors.white.withValues(alpha: 0.35), size: 20),
          ),
          title: Text(section.label, style: TextStyle(
            color: section.enabled ? Colors.white : Colors.white.withValues(alpha: 0.55),
            fontSize: 13, fontWeight: FontWeight.w600,
          )),
          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
            if (section.enabled)
              GestureDetector(
                onTap: onConfigure,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: section.color.withValues(alpha: 0.18),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text('Configurer', style: TextStyle(color: section.color, fontSize: 11, fontWeight: FontWeight.w700)),
                ),
              ),
            const SizedBox(width: 8),
            Switch(
              value: section.enabled,
              onChanged: onToggle,
              activeColor: section.color,
            ),
          ]),
        ),
      ),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Section Configurator Dialog
// ────────────────────────────────────────────────────────────────────────────

class _SectionConfigDialog extends StatefulWidget {
  const _SectionConfigDialog({required this.section, required this.onSave});
  final _SectionConfig section;
  final ValueChanged<Map<String, dynamic>> onSave;

  @override
  State<_SectionConfigDialog> createState() => _SectionConfigDialogState();
}

class _SectionConfigDialogState extends State<_SectionConfigDialog> {
  late Map<String, dynamic> _data;

  // Controllers for simple text fields
  final Map<String, TextEditingController> _controllers = {};

  // Dynamic list items (services, testimonials, faq...)
  List<Map<String, String>> _listItems = [];

  @override
  void initState() {
    super.initState();
    _data = Map<String, dynamic>.from(widget.section.data);

    // Init controllers for known text keys
    for (final key in ['title', 'subtitle', 'body', 'cta_primary', 'cta_secondary', 'founder_name', 'booking_url', 'cta']) {
      if (_data.containsKey(key)) {
        _controllers[key] = TextEditingController(text: _data[key] as String? ?? '');
      }
    }

    // Load list items
    final rawList = _data['items'] ?? _data['plans'] ?? _data['members'] ?? [];
    if (rawList is List) {
      _listItems = rawList.map<Map<String, String>>((e) => Map<String, String>.from(e as Map)).toList();
    }
  }

  @override
  void dispose() {
    for (final c in _controllers.values) c.dispose();
    super.dispose();
  }

  void _save() {
    final result = Map<String, dynamic>.from(_data);
    for (final entry in _controllers.entries) {
      result[entry.key] = entry.value.text.trim();
    }
    // Put list back
    final listKey = _data.containsKey('plans') ? 'plans' : _data.containsKey('members') ? 'members' : 'items';
    result[listKey] = _listItems;
    widget.onSave(result);
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: const Color(0xFF0F172A),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 560, maxHeight: 640),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Header
              Row(children: [
                Container(width: 40, height: 40,
                  decoration: BoxDecoration(color: widget.section.color.withValues(alpha: 0.20), borderRadius: BorderRadius.circular(12)),
                  child: Icon(widget.section.icon, color: widget.section.color, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(widget.section.label, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w800)),
                  Text('Configurer le contenu', style: TextStyle(color: Colors.white.withValues(alpha: 0.45), fontSize: 12)),
                ])),
                IconButton(onPressed: () => Navigator.of(context).pop(), icon: Icon(Icons.close, color: Colors.white.withValues(alpha: 0.50))),
              ]),
              const SizedBox(height: 20),

              // Form content
              Expanded(
                child: SingleChildScrollView(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: _buildFields()),
                ),
              ),
              const SizedBox(height: 16),
              FilledButton.icon(
                onPressed: _save,
                icon: const Icon(Icons.check),
                label: const Text('Enregistrer'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _buildFields() {
    final widgets = <Widget>[];

    void field(String key, String label, String hint, {int maxLines = 1, IconData icon = Icons.edit}) {
      if (_controllers.containsKey(key)) {
        widgets.add(TextField(
          controller: _controllers[key],
          maxLines: maxLines,
          style: const TextStyle(color: Colors.white, fontSize: 14),
          decoration: _dialogInput(label, hint, icon),
        ));
        widgets.add(const SizedBox(height: 12));
      }
    }

    switch (widget.section.type) {
      case 'hero':
        field('title', 'Titre principal', 'Ex : Le goût authentique de Lyon', icon: Icons.title);
        field('subtitle', 'Sous-titre', 'Ex : Depuis 2008, au cœur du Vieux-Lyon', maxLines: 2, icon: Icons.subtitles);
        field('cta_primary', 'Bouton principal', 'Ex : Réserver une table', icon: Icons.touch_app);
        field('cta_secondary', 'Bouton secondaire', 'Ex : Voir le menu', icon: Icons.touch_app_outlined);
        break;

      case 'services':
        field('title', 'Titre de la section', 'Ex : Nos services', icon: Icons.title);
        widgets.add(_ListEditor(
          title: 'Services',
          items: _listItems,
          fields: const [('name', 'Nom du service'), ('desc', 'Description courte'), ('icon', 'Icône (emoji ou mot)')],
          emptyTemplate: {'name': '', 'desc': '', 'icon': ''},
          onChanged: (items) => setState(() => _listItems = items),
        ));
        break;

      case 'about':
        field('title', 'Titre', 'Ex : Notre histoire', icon: Icons.title);
        field('body', 'Texte de présentation', 'Qui vous êtes, votre histoire, vos valeurs...', maxLines: 5, icon: Icons.text_fields);
        field('founder_name', 'Nom du fondateur (optionnel)', 'Ex : Paul Martin', icon: Icons.person_outline);
        break;

      case 'testimonials':
        widgets.add(_ListEditor(
          title: 'Témoignages',
          items: _listItems,
          fields: const [('author', 'Nom'), ('role', 'Rôle/Entreprise'), ('quote', 'Témoignage')],
          emptyTemplate: {'author': '', 'role': '', 'quote': ''},
          onChanged: (items) => setState(() => _listItems = items),
        ));
        break;

      case 'faq':
        widgets.add(_ListEditor(
          title: 'Questions / Réponses',
          items: _listItems,
          fields: const [('q', 'Question'), ('a', 'Réponse')],
          emptyTemplate: {'q': '', 'a': ''},
          onChanged: (items) => setState(() => _listItems = items),
        ));
        break;

      case 'pricing':
        field('title', 'Titre', 'Ex : Nos tarifs', icon: Icons.title);
        widgets.add(_ListEditor(
          title: 'Plans tarifaires',
          items: _listItems,
          fields: const [('name', 'Nom du plan'), ('price', 'Prix (ex: 29€/mois)'), ('features', 'Fonctionnalités (séparées par ;)')],
          emptyTemplate: {'name': '', 'price': '', 'features': ''},
          onChanged: (items) => setState(() => _listItems = items),
        ));
        break;

      case 'gallery':
        field('title', 'Titre', 'Ex : Nos réalisations', icon: Icons.title);
        break;

      case 'contact':
        field('title', 'Titre', 'Ex : Contactez-nous', icon: Icons.title);
        field('subtitle', 'Sous-titre', 'Ex : Réponse sous 24h', icon: Icons.subtitles);
        break;

      case 'booking':
        field('title', 'Titre', 'Ex : Réserver une table', icon: Icons.title);
        field('subtitle', 'Sous-titre', 'Ex : Disponibilités en ligne 24h/24', icon: Icons.subtitles);
        field('booking_url', 'Lien de réservation externe', 'https://calendly.com/...', icon: Icons.link);
        break;

      case 'menu':
        field('title', 'Titre', 'Ex : Notre carte', icon: Icons.title);
        widgets.add(_ListEditor(
          title: 'Plats / Boissons',
          items: _listItems,
          fields: const [('name', 'Nom du plat'), ('description', 'Description'), ('price', 'Prix'), ('category', 'Catégorie')],
          emptyTemplate: {'name': '', 'description': '', 'price': '', 'category': ''},
          onChanged: (items) => setState(() => _listItems = items),
        ));
        break;

      case 'team':
        widgets.add(_ListEditor(
          title: 'Membres de l\'équipe',
          items: _listItems,
          fields: const [('name', 'Nom'), ('role', 'Rôle'), ('bio', 'Courte biographie')],
          emptyTemplate: {'name': '', 'role': '', 'bio': ''},
          onChanged: (items) => setState(() => _listItems = items),
        ));
        break;

      case 'stats':
        widgets.add(_ListEditor(
          title: 'Chiffres clés',
          items: _listItems,
          fields: const [('value', 'Valeur (ex: 500+)'), ('label', 'Libellé (ex: Clients satisfaits)')],
          emptyTemplate: {'value': '', 'label': ''},
          onChanged: (items) => setState(() => _listItems = items),
        ));
        break;

      case 'cta_banner':
        field('title', 'Titre de la bannière', 'Ex : Prêt à démarrer ?', icon: Icons.title);
        field('cta', 'Texte du bouton', 'Ex : Commencer maintenant', icon: Icons.touch_app);
        break;

      default:
        field('title', 'Titre', 'Titre de la section', icon: Icons.title);
        break;
    }

    return widgets;
  }

  InputDecoration _dialogInput(String label, String hint, IconData icon) {
    return InputDecoration(
      labelText: label, hintText: hint,
      prefixIcon: Icon(icon, color: Colors.white.withValues(alpha: 0.38)),
      labelStyle: TextStyle(color: Colors.white.withValues(alpha: 0.62)),
      hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.28)),
      filled: true, fillColor: Colors.white.withValues(alpha: 0.06),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.10))),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppColors.skyBlue, width: 1.4)),
    );
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Dynamic List Editor (for services, testimonials, FAQ, menu items…)
// ────────────────────────────────────────────────────────────────────────────

class _ListEditor extends StatefulWidget {
  const _ListEditor({required this.title, required this.items, required this.fields, required this.emptyTemplate, required this.onChanged});
  final String title;
  final List<Map<String, String>> items;
  final List<(String, String)> fields; // (key, label)
  final Map<String, String> emptyTemplate;
  final ValueChanged<List<Map<String, String>>> onChanged;

  @override
  State<_ListEditor> createState() => _ListEditorState();
}

class _ListEditorState extends State<_ListEditor> {
  late List<Map<String, String>> _items;

  @override
  void initState() {
    super.initState();
    _items = List<Map<String, String>>.from(widget.items);
  }

  void _add() => setState(() {
    _items.add(Map<String, String>.from(widget.emptyTemplate));
    widget.onChanged(_items);
  });

  void _remove(int index) => setState(() {
    _items.removeAt(index);
    widget.onChanged(_items);
  });

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Row(children: [
        Text(widget.title, style: TextStyle(color: Colors.white.withValues(alpha: 0.65), fontSize: 12, fontWeight: FontWeight.w700)),
        const Spacer(),
        GestureDetector(
          onTap: _add,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(color: AppColors.skyBlue.withValues(alpha: 0.18), borderRadius: BorderRadius.circular(8)),
            child: const Text('+ Ajouter', style: TextStyle(color: AppColors.skyBlueAccent, fontSize: 11, fontWeight: FontWeight.w700)),
          ),
        ),
      ]),
      const SizedBox(height: 8),
      ..._items.asMap().entries.map((entry) {
        final i = entry.key;
        final item = entry.value;
        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.04),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Row(children: [
              Text('#${i + 1}', style: TextStyle(color: Colors.white.withValues(alpha: 0.35), fontSize: 11)),
              const Spacer(),
              GestureDetector(
                onTap: () => _remove(i),
                child: Icon(Icons.delete_outline, color: Colors.red.withValues(alpha: 0.65), size: 18),
              ),
            ]),
            const SizedBox(height: 8),
            ...widget.fields.map((f) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: TextField(
                controller: TextEditingController(text: item[f.$1] ?? ''),
                style: const TextStyle(color: Colors.white, fontSize: 13),
                decoration: InputDecoration(
                  labelText: f.$2,
                  labelStyle: TextStyle(color: Colors.white.withValues(alpha: 0.55), fontSize: 12),
                  filled: true, fillColor: Colors.white.withValues(alpha: 0.05),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.08))),
                  focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.skyBlue)),
                ),
                onChanged: (val) {
                  setState(() { item[f.$1] = val; });
                  widget.onChanged(_items);
                },
              ),
            )),
          ]),
        );
      }),
      if (_items.isEmpty)
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.03), borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white.withValues(alpha: 0.07)),
          ),
          child: Text('Aucun élément. Cliquez "+ Ajouter".', style: TextStyle(color: Colors.white.withValues(alpha: 0.35), fontSize: 12), textAlign: TextAlign.center),
        ),
    ]);
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Shared static widgets
// ────────────────────────────────────────────────────────────────────────────

class _Glow extends StatelessWidget {
  const _Glow({required this.color});
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 260, height: 260,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color.withValues(alpha: 0.28),
        boxShadow: [BoxShadow(color: color.withValues(alpha: 0.35), blurRadius: 120, spreadRadius: 40)],
      ),
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
  const _Progress({required this.step, required this.totalSteps, this.scale = 1.0});
  final int step;
  final int totalSteps;
  final double scale;

  @override
  Widget build(BuildContext context) {
    final size = 32.0 * scale;
    final connector = 36.0 * scale;
    
    final List<Widget> children = [];
    for (int i = 0; i < totalSteps; i++) {
      final item = i + 1;
      final done = item < step;
      final active = item == step;
      
      children.add(
        AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          width: size,
          height: size,
          decoration: BoxDecoration(
            color: done
                ? AppColors.skyBlue
                : active
                    ? AppColors.skyBlue.withValues(alpha: 0.18)
                    : Colors.white.withValues(alpha: 0.06),
            border: Border.all(
              color: done || active ? AppColors.skyBlue : Colors.white.withValues(alpha: 0.16),
              width: active ? 2 : 1,
            ),
            shape: BoxShape.circle,
          ),
          child: Center(
            child: done
                ? Icon(Icons.check, color: Colors.white, size: 16 * scale)
                : Text(
                    '$item',
                    style: TextStyle(
                      color: active ? AppColors.skyBlueAccent : Colors.white.withValues(alpha: 0.42),
                      fontWeight: FontWeight.w800,
                      fontSize: 12 * scale,
                    ),
                  ),
          ),
        ),
      );

      if (item < totalSteps) {
        children.add(
          Flexible(
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 220),
              width: connector,
              height: 2,
              margin: EdgeInsets.symmetric(horizontal: 5 * scale),
              color: item < step ? AppColors.skyBlue : Colors.white.withValues(alpha: 0.12),
            ),
          ),
        );
      }
    }

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      mainAxisSize: MainAxisSize.min,
      children: children,
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
      borderRadius: BorderRadius.circular(20),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: selected ? stack.color.withValues(alpha: 0.20) : Colors.white.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: selected ? stack.color : Colors.white.withValues(alpha: 0.12), width: selected ? 2 : 1),
        ),
        child: Stack(children: [
          if (selected) const Positioned(right: 0, top: 0, child: Icon(Icons.check_circle, color: Colors.white, size: 20)),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Container(width: 40, height: 40,
              decoration: BoxDecoration(color: stack.color, borderRadius: BorderRadius.circular(12)),
              child: Icon(stack.icon, color: Colors.white, size: 22),
            ),
            const SizedBox(height: 12),
            Text(stack.label, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            Text(stack.desc, style: TextStyle(color: Colors.white.withValues(alpha: 0.50), fontSize: 11, height: 1.35)),
          ]),
        ]),
      ),
    );
  }
}

class _PremiumCard extends StatelessWidget {
  const _PremiumCard({required this.selected, required this.onTap});
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    const color = Color(0xFFF59E0B);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: selected ? color.withValues(alpha: 0.22) : Colors.white.withValues(alpha: 0.06),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: selected ? color : Colors.white.withValues(alpha: 0.12), width: selected ? 2 : 1),
          boxShadow: selected ? [BoxShadow(color: color.withValues(alpha: 0.18), blurRadius: 28, offset: const Offset(0, 12))] : null,
        ),
        child: Row(children: [
          Container(width: 40, height: 40,
            decoration: BoxDecoration(color: color.withValues(alpha: selected ? 1 : 0.22), borderRadius: BorderRadius.circular(12)),
            child: Icon(Icons.workspace_premium, color: selected ? Colors.white : color, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              const Text('Premium 10K', style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w900)),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(color: color.withValues(alpha: 0.18), borderRadius: BorderRadius.circular(999)),
                child: const Text('Haute qualité', style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w800)),
              ),
            ]),
            const SizedBox(height: 4),
            Text('Pipeline IA avancé : stratégie, UX, QA et raffinement. One Page ou Multi Page.',
                style: TextStyle(color: Colors.white.withValues(alpha: 0.52), fontSize: 11, height: 1.35)),
          ])),
          const SizedBox(width: 10),
          Icon(selected ? Icons.check_circle : Icons.radio_button_unchecked, color: selected ? color : Colors.white.withValues(alpha: 0.38)),
        ]),
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
    return Row(children: [
      Container(width: 44 * scale, height: 44 * scale,
        decoration: BoxDecoration(color: color.withValues(alpha: 0.22), borderRadius: BorderRadius.circular(14 * scale)),
        child: Icon(icon, color: color, size: 22 * scale),
      ),
      SizedBox(width: 14 * scale),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: TextStyle(color: Colors.white, fontSize: 21 * scale, fontWeight: FontWeight.w800)),
        SizedBox(height: 2 * scale),
        Text(subtitle, style: TextStyle(color: Colors.white.withValues(alpha: 0.45), fontSize: 12 * scale)),
      ])),
    ]);
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
  const _ResponsiveActions({required this.back, required this.next, required this.backLabel, required this.nextLabel, this.nextIcon = const Icon(Icons.arrow_forward)});
  final VoidCallback? back;
  final VoidCallback? next;
  final String backLabel;
  final String nextLabel;
  final Widget nextIcon;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      final stacked = constraints.maxWidth < 360;
      final backBtn = OutlinedButton.icon(onPressed: back, icon: const Icon(Icons.arrow_back), label: Text(backLabel, overflow: TextOverflow.ellipsis));
      final nextBtn = FilledButton.icon(onPressed: next, icon: nextIcon, label: Text(nextLabel, overflow: TextOverflow.ellipsis));
      if (stacked) {
        return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [nextBtn, const SizedBox(height: 10), backBtn]);
      }
      return Row(children: [Flexible(child: backBtn), const SizedBox(width: 12), Expanded(flex: 2, child: nextBtn)]);
    });
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
        filled: true, fillColor: Colors.white.withValues(alpha: 0.06),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.10))),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: AppColors.skyBlue, width: 1.6)),
      ),
      items: values.map((v) => DropdownMenuItem(value: v, child: Text(v))).toList(),
      onChanged: (v) { if (v != null) onChanged(v); },
    );
  }
}

class _FontPickerDropdown extends StatelessWidget {
  const _FontPickerDropdown({required this.value, required this.options, required this.label, required this.onChanged});
  final String value;
  final List<_FontOption> options;
  final String label;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      DropdownButtonFormField<String>(
        value: value.isEmpty ? options.first.label : value,
        dropdownColor: const Color(0xFF0F172A),
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: TextStyle(color: Colors.white.withValues(alpha: 0.62)),
          filled: true, fillColor: Colors.white.withValues(alpha: 0.06),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.10))),
          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: AppColors.skyBlue, width: 1.6)),
        ),
        items: options.map((f) => DropdownMenuItem<String>(value: f.label, child: Text('${f.label} · ${f.category}'))).toList(),
        onChanged: (val) { if (val != null) onChanged(val); },
      ),
      if (value.isNotEmpty) ...[
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(11),
          decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.04), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white.withValues(alpha: 0.08))),
          child: const Text('Aperçu — The quick brown fox jumps over the lazy dog', style: TextStyle(color: Colors.white70, fontSize: 12)),
        ),
      ],
    ]);
  }
}

class _ColorPickers extends StatefulWidget {
  const _ColorPickers({required this.primaryColor, required this.secondaryColor, required this.onPrimaryChanged, required this.onSecondaryChanged});
  final Color primaryColor;
  final Color secondaryColor;
  final ValueChanged<Color> onPrimaryChanged;
  final ValueChanged<Color> onSecondaryChanged;

  @override
  State<_ColorPickers> createState() => _ColorPickersState();
}

class _ColorPickersState extends State<_ColorPickers> {
  void _openColorPicker(String title, Color initial, ValueChanged<Color> onChanged) {
    Color picked = initial;
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF0F172A),
        title: Text('Choisir la couleur $title', style: const TextStyle(color: Colors.white)),
        content: SingleChildScrollView(
          child: ColorPicker(pickerColor: initial, onColorChanged: (c) => picked = c, pickerAreaHeightPercent: 0.8, enableAlpha: false, displayThumbColor: true),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Annuler')),
          FilledButton(onPressed: () { onChanged(picked); Navigator.of(context).pop(); }, child: const Text('Sélectionner')),
        ],
      ),
    );
  }

  String _hex(Color c) => '#${c.value.toRadixString(16).substring(2).toUpperCase()}';

  Widget _swatch(String label, Color color, VoidCallback onTap) {
    return Expanded(child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.06), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white.withValues(alpha: 0.10))),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.58), fontSize: 11)),
          const SizedBox(height: 10),
          Row(children: [
            Container(width: 28, height: 28, decoration: BoxDecoration(color: color, shape: BoxShape.circle, border: Border.all(color: Colors.white70, width: 2))),
            const SizedBox(width: 8),
            Text(_hex(color), style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
          ]),
        ]),
      ),
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      _swatch('Couleur principale', widget.primaryColor, () => _openColorPicker('principale', widget.primaryColor, widget.onPrimaryChanged)),
      const SizedBox(width: 12),
      _swatch('Couleur secondaire', widget.secondaryColor, () => _openColorPicker('secondaire', widget.secondaryColor, widget.onSecondaryChanged)),
    ]);
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
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.06), borderRadius: BorderRadius.circular(14), border: Border.all(color: Colors.white.withValues(alpha: 0.10))),
      child: Row(children: [
        Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.48))),
        const Spacer(),
        Flexible(child: Text(value, textAlign: TextAlign.right, style: TextStyle(color: accent ? AppColors.skyBlueAccent : Colors.white, fontWeight: FontWeight.w700))),
      ]),
    );
  }
}
