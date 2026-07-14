import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/token_store.dart';

enum AuthStatus { loading, authenticated, unauthenticated }

final authSessionProvider =
    StateNotifierProvider<AuthSessionController, AuthStatus>((ref) {
  return AuthSessionController(ref.watch(tokenStoreProvider));
});

class AuthSessionController extends StateNotifier<AuthStatus> {
  AuthSessionController(this._tokens) : super(AuthStatus.loading) {
    _restore();
  }

  final TokenStore _tokens;

  Future<void> _restore() async {
    state = await _tokens.hasSession()
        ? AuthStatus.authenticated
        : AuthStatus.unauthenticated;
  }

  void authenticated() => state = AuthStatus.authenticated;

  Future<void> logout() async {
    await _tokens.clear();
    state = AuthStatus.unauthenticated;
  }

  void expired() => state = AuthStatus.unauthenticated;
}
