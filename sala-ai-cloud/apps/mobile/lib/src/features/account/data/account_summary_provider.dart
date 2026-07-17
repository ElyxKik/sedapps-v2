import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/api_client.dart';

class AccountSummary {
  const AccountSummary({
    required this.name,
    required this.email,
  });

  factory AccountSummary.fromJson(Map<String, dynamic> json) {
    final email = json['email']?.toString().trim() ?? '';
    final fullName = json['full_name']?.toString().trim() ?? '';
    final fallback =
        email.contains('@') ? email.split('@').first : 'Mon compte';
    return AccountSummary(
      name: fullName.isEmpty ? fallback : fullName,
      email: email,
    );
  }

  final String name;
  final String email;

  String get firstName {
    final parts = name.trim().split(RegExp(r'\s+'));
    return parts.isEmpty || parts.first.isEmpty ? 'Compte' : parts.first;
  }

  String get initials {
    final parts = name
        .trim()
        .split(RegExp(r'\s+'))
        .where((part) => part.isNotEmpty)
        .take(2)
        .toList();
    if (parts.isEmpty) return 'S';
    return parts.map((part) => part[0].toUpperCase()).join();
  }
}

final accountSummaryProvider =
    FutureProvider.autoDispose<AccountSummary>((ref) async {
  final account = await ref.watch(apiClientProvider).account();
  return AccountSummary.fromJson(account);
});
