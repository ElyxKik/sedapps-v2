import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

final localizationProvider =
    StateNotifierProvider<LocalizationNotifier, String>((ref) {
  return LocalizationNotifier();
});

class LocalizationNotifier extends StateNotifier<String> {
  static const _languageKey = 'app_language';
  static const _supportedLanguages = ['Français', 'English'];

  LocalizationNotifier() : super('Français') {
    _loadLanguage();
  }

  Future<void> _loadLanguage() async {
    final prefs = await SharedPreferences.getInstance();
    final language = prefs.getString(_languageKey) ?? 'Français';
    if (_supportedLanguages.contains(language)) {
      state = language;
    }
  }

  Future<void> setLanguage(String language) async {
    if (!_supportedLanguages.contains(language)) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_languageKey, language);
    state = language;
  }

  String get languageCode => state == 'English' ? 'en' : 'fr';

  Map<String, String> get translations {
    if (state == 'English') {
      return _englishTranslations;
    }
    return _frenchTranslations;
  }

  static const _frenchTranslations = {
    'my_account': 'Mon compte',
    'manage_profile': 'Gère ton profil, ta facturation et tes préférences',
    'settings': 'Paramètres',
    'billing': 'Facturation',
    'manage_info': 'Gérer les informations',
    'domains': 'Domaines',
    'manage_domains': 'Gérer les domaines',
    'notifications': 'Notifications',
    'security': 'Sécurité',
    'preferences': 'Préférences',
    'language': 'Langue',
    'theme': 'Thème',
    'timezone': 'Fuseau horaire',
    'logout': 'Se déconnecter',
    'edit_profile': 'Modifier le profil',
    'save': 'Enregistrer',
    'cancel': 'Annuler',
    'full_name': 'Nom complet',
    'organization': 'Organisation',
    'email': 'Email',
    'profile_updated': 'Profil mis à jour',
    'error_updating_profile': 'Erreur lors de la mise à jour du profil',
  };

  static const _englishTranslations = {
    'my_account': 'My Account',
    'manage_profile': 'Manage your profile, billing and preferences',
    'settings': 'Settings',
    'billing': 'Billing',
    'manage_info': 'Manage information',
    'domains': 'Domains',
    'manage_domains': 'Manage domains',
    'notifications': 'Notifications',
    'security': 'Security',
    'preferences': 'Preferences',
    'language': 'Language',
    'theme': 'Theme',
    'timezone': 'Timezone',
    'logout': 'Logout',
    'edit_profile': 'Edit Profile',
    'save': 'Save',
    'cancel': 'Cancel',
    'full_name': 'Full Name',
    'organization': 'Organization',
    'email': 'Email',
    'profile_updated': 'Profile updated',
    'error_updating_profile': 'Error updating profile',
  };
}
