import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/api_client.dart';

abstract interface class AuthRepository {
  Future<void> login(String email, String password);
  Future<void> register({
    required String email,
    required String password,
    required String organizationName,
    required String fullName,
  });
}

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return ApiAuthRepository(ref.watch(apiClientProvider));
});

class ApiAuthRepository implements AuthRepository {
  const ApiAuthRepository(this._api);

  final ApiClient _api;

  @override
  Future<void> login(String email, String password) =>
      _api.login(email, password);

  @override
  Future<void> register({
    required String email,
    required String password,
    required String organizationName,
    required String fullName,
  }) =>
      _api.register(email, password, organizationName, fullName);
}
