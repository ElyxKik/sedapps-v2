class BillingPlan {
  const BillingPlan({
    required this.id,
    required this.slug,
    required this.name,
    required this.description,
    required this.billingInterval,
    required this.priceCents,
    required this.currency,
    required this.monthlyCredits,
    required this.checkoutEnabled,
  });

  factory BillingPlan.fromJson(Map<String, dynamic> json) => BillingPlan(
        id: json['id']?.toString() ?? '',
        slug: json['slug']?.toString() ?? '',
        name: json['name']?.toString() ?? 'Plan',
        description: json['description']?.toString() ?? '',
        billingInterval: json['billing_interval']?.toString() ?? 'month',
        priceCents: (json['price_cents'] as num?)?.toInt() ?? 0,
        currency: json['currency']?.toString() ?? 'EUR',
        monthlyCredits: (json['monthly_credits'] as num?)?.toInt() ?? 0,
        checkoutEnabled: json['checkout_enabled'] == true,
      );

  final String id;
  final String slug;
  final String name;
  final String description;
  final String billingInterval;
  final int priceCents;
  final String currency;
  final int monthlyCredits;
  final bool checkoutEnabled;

  bool get isFree => priceCents == 0 || slug == 'free';
  bool get isYearly => billingInterval == 'year';
}

class BillingCheckout {
  const BillingCheckout({required this.checkoutUrl, this.purchaseId});

  factory BillingCheckout.fromJson(Map<String, dynamic> json) =>
      BillingCheckout(
        checkoutUrl: json['checkout_url']?.toString() ?? '',
        purchaseId: json['purchase_id']?.toString(),
      );

  final String checkoutUrl;
  final String? purchaseId;
}
