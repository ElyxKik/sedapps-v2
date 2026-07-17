import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/config.dart';
import '../../data/mock_data.dart';
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
    final refreshToken = await _tokens.refreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      state = AuthStatus.unauthenticated;
      return;
    }
    if (useMockData) {
      state = AuthStatus.authenticated;
      return;
    }
    try {
      final response = await Dio(BaseOptions(
        baseUrl: AppConfig.coreApiBaseUrl,
        connectTimeout: const Duration(seconds: 12),
        receiveTimeout: const Duration(seconds: 12),
      )).post('/v1/auth/refresh', data: {'refresh_token': refreshToken});
      final data = Map<String, dynamic>.from(response.data as Map);
      final accessToken = data['access_token']?.toString() ?? '';
      final rotatedRefreshToken = data['refresh_token']?.toString() ?? '';
      if (accessToken.isEmpty || rotatedRefreshToken.isEmpty) {
        throw const FormatException('invalid refresh response');
      }
      await _tokens.save(
        accessToken: accessToken,
        refreshToken: rotatedRefreshToken,
      );
      state = AuthStatus.authenticated;
    } catch (_) {
      await _tokens.clear();
      state = AuthStatus.unauthenticated;
    }
  }

  void authenticated() => state = AuthStatus.authenticated;

  Future<void> logout() async {
    await _tokens.clear();
    state = AuthStatus.unauthenticated;
  }

  void expired() => state = AuthStatus.unauthenticated;
}
