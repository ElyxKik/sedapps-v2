import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/api_client.dart';
import '../domain/billing_plan.dart';
import '../domain/credit_wallet.dart';

abstract interface class BillingRepository {
  Future<CreditWallet> wallet();
  Future<List<BillingPlan>> plans();
  Future<BillingCheckout> checkout({
    required String planId,
    required String phoneNumber,
    required String countryCode,
    String? discountCode,
  });
}

final billingRepositoryProvider = Provider<BillingRepository>((ref) {
  return ApiBillingRepository(ref.watch(apiClientProvider));
});

class ApiBillingRepository implements BillingRepository {
  const ApiBillingRepository(this._api);

  final ApiClient _api;

  @override
  Future<CreditWallet> wallet() async =>
      CreditWallet.fromJson(await _api.creditWallet());

  @override
  Future<List<BillingPlan>> plans() async => (await _api.billingPlans())
      .map(BillingPlan.fromJson)
      .toList(growable: false);

  @override
  Future<BillingCheckout> checkout({
    required String planId,
    required String phoneNumber,
    required String countryCode,
    String? discountCode,
  }) async =>
      BillingCheckout.fromJson(await _api.createBillingCheckout(
        planId: planId,
        phoneNumber: phoneNumber,
        countryCode: countryCode,
        discountCode: discountCode,
      ));
}

final creditWalletProvider = FutureProvider<CreditWallet>((ref) {
  return ref.watch(billingRepositoryProvider).wallet();
});
