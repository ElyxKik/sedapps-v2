import 'dart:async';
import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

class CacheService {
  static const _prefix = 'cache_';
  static const _ttlPrefix = 'ttl_';

  final SharedPreferences _prefs;

  CacheService(this._prefs);

  Future<void> set(String key, dynamic value, {Duration? ttl}) async {
    final cacheKey = '$_prefix$key';
    final jsonValue = jsonEncode(value);

    await _prefs.setString(cacheKey, jsonValue);

    if (ttl != null) {
      final expiresAt = DateTime.now().add(ttl).millisecondsSinceEpoch;
      await _prefs.setInt('$_ttlPrefix$key', expiresAt);
    }
  }

  T? get<T>(String key, {T Function(dynamic)? fromJson}) {
    final cacheKey = '$_prefix$key';
    final ttlKey = '$_ttlPrefix$key';

    final expiresAt = _prefs.getInt(ttlKey);
    if (expiresAt != null && DateTime.now().millisecondsSinceEpoch > expiresAt) {
      remove(key);
      return null;
    }

    final value = _prefs.getString(cacheKey);
    if (value == null) return null;

    try {
      final decoded = jsonDecode(value);
      return fromJson != null ? fromJson(decoded) : decoded as T;
    } catch (_) {
      return null;
    }
  }

  Future<void> remove(String key) async {
    await _prefs.remove('$_prefix$key');
    await _prefs.remove('$_ttlPrefix$key');
  }

  Future<void> clear() async {
    final keys = _prefs.getKeys();
    for (final key in keys) {
      if (key.startsWith(_prefix)) {
        await _prefs.remove(key);
      }
    }
  }

  bool has(String key) {
    final ttlKey = '$_ttlPrefix$key';
    final expiresAt = _prefs.getInt(ttlKey);

    if (expiresAt != null && DateTime.now().millisecondsSinceEpoch > expiresAt) {
      remove(key);
      return false;
    }

    return _prefs.containsKey('$_prefix$key');
  }
}

final cacheServiceProvider = FutureProvider<CacheService>((ref) async {
  final prefs = await SharedPreferences.getInstance();
  return CacheService(prefs);
});
