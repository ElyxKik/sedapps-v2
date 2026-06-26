import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/theme.dart';

final themeProvider = StateNotifierProvider<ThemeNotifier, ThemeMode>((ref) {
  return ThemeNotifier();
});

class ThemeNotifier extends StateNotifier<ThemeMode> {
  static const _themeKey = 'app_theme_mode';

  ThemeNotifier() : super(ThemeMode.light) {
    _loadTheme();
  }

  Future<void> _loadTheme() async {
    final prefs = await SharedPreferences.getInstance();
    final themeName = prefs.getString(_themeKey) ?? 'Clair';
    state = _nameToThemeMode(themeName);
  }

  Future<void> setTheme(String themeName) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_themeKey, themeName);
    state = _nameToThemeMode(themeName);
  }

  ThemeMode _nameToThemeMode(String name) {
    switch (name) {
      case 'Sombre':
        return ThemeMode.dark;
      case 'Système':
        return ThemeMode.system;
      default:
        return ThemeMode.light;
    }
  }

  String getCurrentThemeName() {
    switch (state) {
      case ThemeMode.dark:
        return 'Sombre';
      case ThemeMode.system:
        return 'Système';
      default:
        return 'Clair';
    }
  }
}
