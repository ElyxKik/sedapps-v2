class CreditWallet {
  const CreditWallet({
    required this.balance,
    required this.reserved,
    required this.available,
    required this.usedThisMonth,
    required this.monthlyQuota,
    required this.plan,
    required this.tokensPerCredit,
    this.resetAt,
  });

  factory CreditWallet.fromJson(Map<String, dynamic> json) => CreditWallet(
        balance: _integer(json['balance_credits']),
        reserved: _integer(json['reserved_credits']),
        available: _integer(json['available_credits']),
        usedThisMonth: _integer(json['used_this_month_credits']),
        monthlyQuota: _integer(json['monthly_quota_credits']),
        plan: json['plan']?.toString() ?? 'free',
        tokensPerCredit: _integer(json['tokens_per_credit']),
        resetAt: DateTime.tryParse(json['reset_at']?.toString() ?? ''),
      );

  static int _integer(Object? value) => (value as num?)?.toInt() ?? 0;

  final int balance;
  final int reserved;
  final int available;
  final int usedThisMonth;
  final int monthlyQuota;
  final String plan;
  final int tokensPerCredit;
  final DateTime? resetAt;

  double get usageRatio => monthlyQuota == 0
      ? 0
      : (usedThisMonth / monthlyQuota).clamp(0, 1).toDouble();
}
