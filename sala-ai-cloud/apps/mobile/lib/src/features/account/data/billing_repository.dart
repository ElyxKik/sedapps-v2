import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/api_client.dart';
import '../domain/credit_wallet.dart';

abstract interface class BillingRepository {
  Future<CreditWallet> wallet();
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
}

final creditWalletProvider = FutureProvider<CreditWallet>((ref) {
  return ref.watch(billingRepositoryProvider).wallet();
});
