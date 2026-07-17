import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:dio/dio.dart';

import '../../core/theme.dart';
import 'data/billing_repository.dart';
import 'domain/billing_plan.dart';
import 'domain/credit_wallet.dart';

Future<void> showSubscriptionDialog({
  required BuildContext context,
  required BillingRepository repository,
}) =>
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (_) => _SubscriptionDialog(repository: repository),
    );

class _SubscriptionDialog extends StatefulWidget {
  const _SubscriptionDialog({required this.repository});

  final BillingRepository repository;

  @override
  State<_SubscriptionDialog> createState() => _SubscriptionDialogState();
}

class _SubscriptionDialogState extends State<_SubscriptionDialog> {
  final _phoneController = TextEditingController();
  final _discountController = TextEditingController();
  late Future<({List<BillingPlan> plans, CreditWallet wallet})> _data;
  String _interval = 'month';
  String _countryCode = 'CD';
  String? _selectedPlanId;
  bool _submitting = false;
  String? _error;

  static const _countries = {
    'CD': 'RD Congo (+243)',
    'CG': 'Congo (+242)',
    'FR': 'France (+33)',
    'BE': 'Belgique (+32)',
    'CA': 'Canada (+1)',
    'US': 'États-Unis (+1)',
    'CI': 'Côte d’Ivoire (+225)',
    'SN': 'Sénégal (+221)',
  };

  static const _phoneRules = <String, ({String dialCode, int length})>{
    'CD': (dialCode: '243', length: 9),
    'CG': (dialCode: '242', length: 9),
    'FR': (dialCode: '33', length: 9),
    'BE': (dialCode: '32', length: 9),
    'CA': (dialCode: '1', length: 10),
    'US': (dialCode: '1', length: 10),
    'CI': (dialCode: '225', length: 10),
    'SN': (dialCode: '221', length: 9),
  };

  @override
  void initState() {
    super.initState();
    _data = _load();
    _phoneController.addListener(_refreshPhoneValidation);
  }

  void _refreshPhoneValidation() {
    if (mounted) setState(() {});
  }

  Future<({List<BillingPlan> plans, CreditWallet wallet})> _load() async {
    final plans = await widget.repository.plans();
    final wallet = await widget.repository.wallet();
    final paidPlans = plans.where((plan) => !plan.isFree).toList();
    final hasMonthlyPlans =
        paidPlans.any((plan) => plan.billingInterval == 'month');
    final hasYearlyPlans =
        paidPlans.any((plan) => plan.billingInterval == 'year');
    final currentIsYearly = paidPlans.any(
        (plan) => plan.slug == wallet.plan && plan.billingInterval == 'year');
    if ((currentIsYearly && hasYearlyPlans) || !hasMonthlyPlans) {
      _interval = 'year';
    } else {
      _interval = 'month';
    }
    return (plans: plans, wallet: wallet);
  }

  @override
  void dispose() {
    _phoneController.removeListener(_refreshPhoneValidation);
    _phoneController.dispose();
    _discountController.dispose();
    super.dispose();
  }

  String _price(BillingPlan plan) {
    if (plan.isFree) return 'Gratuit';
    final formatter = NumberFormat.currency(
      locale: 'fr_FR',
      name: plan.currency,
      decimalDigits: plan.priceCents % 100 == 0 ? 0 : 2,
    );
    return formatter.format(plan.priceCents / 100);
  }

  Future<void> _checkout(BillingPlan plan) async {
    final phone = _normalizedPhone();
    final rule = _phoneRules[_countryCode];
    if (phone == null) {
      setState(() => _error = rule == null
          ? 'Entre un numéro de téléphone valide.'
          : 'Numéro invalide : ${rule.length} chiffres attendus après +${rule.dialCode}.');
      return;
    }
    setState(() {
      _submitting = true;
      _selectedPlanId = plan.id;
      _error = null;
    });
    try {
      final checkout = await widget.repository.checkout(
        planId: plan.id,
        phoneNumber: phone,
        countryCode: _countryCode,
        discountCode: _discountController.text,
      );
      final uri = Uri.tryParse(checkout.checkoutUrl);
      if (uri == null || !uri.isScheme('https')) {
        throw Exception('Lien de paiement Chariow invalide.');
      }
      final opened = await launchUrl(
        uri,
        mode: kIsWeb
            ? LaunchMode.platformDefault
            : LaunchMode.externalApplication,
        webOnlyWindowName: kIsWeb ? '_self' : null,
      );
      if (!opened) throw Exception('Impossible d’ouvrir la page de paiement.');
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  String? _normalizedPhone() {
    var value = _phoneController.text.trim();
    if (value.startsWith('00')) value = value.substring(2);
    final rule = _phoneRules[_countryCode];
    if (rule == null) {
      value = value.replaceFirst(RegExp(r'^0+'), '');
      return value.length >= 7 && value.length <= 15 ? value : null;
    }
    if (value.startsWith(rule.dialCode) &&
        value.length == rule.dialCode.length + rule.length) {
      value = value.substring(rule.dialCode.length);
    }
    if (value.startsWith('0') && value.length == rule.length + 1) {
      value = value.substring(1);
    }
    return value.length == rule.length ? value : null;
  }

  bool get _hasValidPhone => _normalizedPhone() != null;

  String _friendlyError(Object error) {
    if (error is DioException) {
      final data = error.response?.data;
      if (data is Map) {
        final detail = data['detail'];
        if (detail is String && detail.trim().isNotEmpty) {
          return detail.trim();
        }
        if (detail is Map && detail['message'] != null) {
          return detail['message'].toString();
        }
      }
      final nested = error.error;
      if (nested != null && nested.toString().trim().isNotEmpty) {
        return nested.toString().replaceFirst('Exception: ', '');
      }
    }
    final text = error.toString().replaceFirst('Exception: ', '');
    if (text.contains('503')) {
      return 'Le paiement est temporairement indisponible.';
    }
    return text.isEmpty ? 'Impossible de préparer le paiement.' : text;
  }

  @override
  Widget build(BuildContext context) {
    final compact = MediaQuery.sizeOf(context).width < 720;
    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: EdgeInsets.all(compact ? 10 : 28),
      child: Container(
        width: 980,
        constraints: BoxConstraints(
          maxHeight: MediaQuery.sizeOf(context).height - (compact ? 20 : 56),
        ),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(compact ? 20 : 28),
          border: Border.all(color: AppColors.border),
          boxShadow: const [
            BoxShadow(
                color: Colors.black54, blurRadius: 48, offset: Offset(0, 20)),
          ],
        ),
        child: FutureBuilder<({List<BillingPlan> plans, CreditWallet wallet})>(
          future: _data,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const SizedBox(
                height: 420,
                child: Center(child: CircularProgressIndicator()),
              );
            }
            if (snapshot.hasError) return _loadError();
            return _content(snapshot.requireData, compact);
          },
        ),
      ),
    );
  }

  Widget _loadError() => SizedBox(
        height: 360,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.cloud_off_outlined,
                size: 44, color: AppColors.danger),
            const SizedBox(height: 14),
            const Text('Impossible de charger les abonnements.',
                style: TextStyle(fontWeight: FontWeight.w800, fontSize: 17)),
            const SizedBox(height: 18),
            FilledButton.tonal(
              onPressed: () => setState(() => _data = _load()),
              child: const Text('Réessayer'),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Fermer'),
            ),
          ],
        ),
      );

  Widget _content(
      ({List<BillingPlan> plans, CreditWallet wallet}) data, bool compact) {
    final paidPlans = data.plans.where((plan) => !plan.isFree).toList();
    final hasMonthlyPlans =
        paidPlans.any((plan) => plan.billingInterval == 'month');
    final hasYearlyPlans =
        paidPlans.any((plan) => plan.billingInterval == 'year');
    final plans = paidPlans
        .where((plan) => plan.billingInterval == _interval)
        .toList(growable: false);
    return Column(
      children: [
        Padding(
          padding: EdgeInsets.fromLTRB(compact ? 18 : 28, 20, 14, 16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                    gradient: AppColors.heroGradient,
                    borderRadius: BorderRadius.circular(15)),
                child: const Icon(Icons.workspace_premium_outlined,
                    color: Colors.white),
              ),
              const SizedBox(width: 14),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Choisir ton abonnement',
                        style: TextStyle(
                            fontSize: 21, fontWeight: FontWeight.w900)),
                    SizedBox(height: 3),
                    Text(
                        'Plus de crédits, plus de créations. Paiement sécurisé par Chariow.',
                        style: TextStyle(
                            color: AppColors.textSecondary, fontSize: 12)),
                  ],
                ),
              ),
              IconButton(
                  onPressed: _submitting ? null : () => Navigator.pop(context),
                  icon: const Icon(Icons.close)),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: SingleChildScrollView(
            padding: EdgeInsets.all(compact ? 16 : 28),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    if (hasMonthlyPlans || hasYearlyPlans)
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                            color: AppColors.surfaceMuted,
                            borderRadius: BorderRadius.circular(13)),
                        child: Row(mainAxisSize: MainAxisSize.min, children: [
                          if (hasMonthlyPlans)
                            _intervalButton('month', 'Mensuel'),
                          if (hasYearlyPlans) _intervalButton('year', 'Annuel'),
                        ]),
                      ),
                    _CurrentPlanChip(plan: data.wallet.plan),
                  ],
                ),
                const SizedBox(height: 20),
                _billingDetails(),
                const SizedBox(height: 24),
                if (plans.isEmpty)
                  const _EmptyInterval()
                else
                  LayoutBuilder(builder: (context, constraints) {
                    final columns = compact ? 1 : (plans.length >= 3 ? 3 : 2);
                    final width = columns == 1
                        ? constraints.maxWidth
                        : (constraints.maxWidth - (columns - 1) * 14) / columns;
                    return Wrap(
                      spacing: 14,
                      runSpacing: 14,
                      children: [
                        for (final plan in plans)
                          SizedBox(
                            width: width,
                            child: _planCard(plan, data.wallet.plan),
                          ),
                      ],
                    );
                  }),
                if (_error != null) ...[
                  const SizedBox(height: 14),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(13),
                    decoration: BoxDecoration(
                        color: AppColors.danger.withValues(alpha: .1),
                        borderRadius: BorderRadius.circular(12)),
                    child: Text(_error!,
                        style: const TextStyle(
                            color: AppColors.danger, fontSize: 13)),
                  ),
                ],
                const SizedBox(height: 14),
                const Row(children: [
                  Icon(Icons.lock_outline, size: 16, color: AppColors.success),
                  SizedBox(width: 7),
                  Expanded(
                    child: Text(
                      'La licence reste protégée sur Sala AI. Après paiement, ta facture est envoyée par email.',
                      style: TextStyle(
                          color: AppColors.textSecondary, fontSize: 11),
                    ),
                  ),
                ]),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _intervalButton(String value, String label) => InkWell(
        onTap: _submitting ? null : () => setState(() => _interval = value),
        borderRadius: BorderRadius.circular(10),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 9),
          decoration: BoxDecoration(
            color: _interval == value ? AppColors.primary : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(label,
              style: TextStyle(
                  fontWeight: FontWeight.w800,
                  color: _interval == value
                      ? Colors.white
                      : AppColors.textSecondary)),
        ),
      );

  Widget _planCard(BillingPlan plan, String currentPlan) {
    final current = plan.slug == currentPlan;
    final processing = _submitting && _selectedPlanId == plan.id;
    final canCheckout = _hasValidPhone &&
        !current &&
        !plan.isFree &&
        plan.checkoutEnabled &&
        !_submitting;
    return AnimatedContainer(
      duration: const Duration(milliseconds: 180),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: current
            ? LinearGradient(colors: [
                AppColors.primary.withValues(alpha: .18),
                AppColors.cyan.withValues(alpha: .06),
              ])
            : null,
        color: current ? null : AppColors.surfaceMuted,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
            color: current ? AppColors.primaryLight : AppColors.borderSoft,
            width: current ? 1.5 : 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Expanded(
              child: Text(plan.name,
                  style: const TextStyle(
                      fontWeight: FontWeight.w900, fontSize: 17)),
            ),
            if (current)
              const Icon(Icons.verified, color: AppColors.success, size: 20),
          ]),
          const SizedBox(height: 8),
          Text(_price(plan),
              style:
                  const TextStyle(fontWeight: FontWeight.w900, fontSize: 25)),
          if (!plan.isFree)
            Text(plan.isYearly ? 'par an' : 'par mois',
                style: const TextStyle(
                    color: AppColors.textSecondary, fontSize: 11)),
          const SizedBox(height: 14),
          Text(
              plan.description.isEmpty
                  ? 'Une offre Sala AI adaptée à tes besoins.'
                  : plan.description,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                  color: AppColors.textSecondary, fontSize: 12)),
          const SizedBox(height: 14),
          _benefit(
              Icons.auto_awesome, '${plan.monthlyCredits} crédits IA / mois'),
          const SizedBox(height: 7),
          _benefit(Icons.data_usage,
              '${plan.monthlyCredits * 1000} tokens IA inclus'),
          const SizedBox(height: 18),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: canCheckout ? () => _checkout(plan) : null,
              child: processing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : Text(current
                      ? 'Plan actuel'
                      : !plan.checkoutEnabled
                          ? 'Bientôt disponible'
                          : !_hasValidPhone
                              ? 'Ajoute ton numéro'
                              : 'Choisir ${plan.name}'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _benefit(IconData icon, String text) => Row(children: [
        Icon(icon, size: 16, color: AppColors.cyan),
        const SizedBox(width: 7),
        Expanded(child: Text(text, style: const TextStyle(fontSize: 11))),
      ]);

  Widget _billingDetails() => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.background.withValues(alpha: .6),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.borderSoft),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('1. Ton numéro pour le paiement',
                style: TextStyle(fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            const Text(
                'Renseigne-le avant de choisir une offre. Chariow l’utilise pour préparer le paiement sécurisé.',
                style: TextStyle(color: AppColors.textSecondary, fontSize: 11)),
            const SizedBox(height: 14),
            LayoutBuilder(builder: (context, constraints) {
              final narrow = constraints.maxWidth < 580;
              final country = DropdownButtonFormField<String>(
                initialValue: _countryCode,
                decoration: const InputDecoration(labelText: 'Pays'),
                items: _countries.entries
                    .map((entry) => DropdownMenuItem(
                        value: entry.key, child: Text(entry.value)))
                    .toList(),
                onChanged: _submitting
                    ? null
                    : (value) => setState(() => _countryCode = value ?? 'CD'),
              );
              final phone = TextField(
                controller: _phoneController,
                enabled: !_submitting,
                keyboardType: TextInputType.phone,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                decoration: InputDecoration(
                  labelText: 'Téléphone',
                  prefixText: '+${_phoneRules[_countryCode]?.dialCode ?? ''} ',
                  hintText:
                      _countryCode == 'CD' ? '812345678' : 'Numéro national',
                  helperText: 'L’indicatif est ajouté automatiquement.',
                ),
              );
              if (narrow) {
                return Column(
                    children: [country, const SizedBox(height: 12), phone]);
              }
              return Row(children: [
                Expanded(flex: 2, child: country),
                const SizedBox(width: 12),
                Expanded(flex: 3, child: phone),
              ]);
            }),
            const SizedBox(height: 12),
            TextField(
              controller: _discountController,
              enabled: !_submitting,
              textCapitalization: TextCapitalization.characters,
              decoration: const InputDecoration(
                labelText: 'Code promo (facultatif)',
                prefixIcon: Icon(Icons.sell_outlined),
              ),
            ),
          ],
        ),
      );
}

class _CurrentPlanChip extends StatelessWidget {
  const _CurrentPlanChip({required this.plan});
  final String plan;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
        decoration: BoxDecoration(
            color: AppColors.success.withValues(alpha: .1),
            borderRadius: BorderRadius.circular(12)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.verified_outlined,
              size: 17, color: AppColors.success),
          const SizedBox(width: 7),
          Text('Plan actuel : $plan',
              style:
                  const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
        ]),
      );
}

class _EmptyInterval extends StatelessWidget {
  const _EmptyInterval();

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(28),
        decoration: BoxDecoration(
            color: AppColors.surfaceMuted,
            borderRadius: BorderRadius.circular(18)),
        child: const Column(children: [
          Icon(Icons.event_busy_outlined, color: AppColors.textSecondary),
          SizedBox(height: 8),
          Text('Aucune offre disponible pour cette période.'),
        ]),
      );
}
