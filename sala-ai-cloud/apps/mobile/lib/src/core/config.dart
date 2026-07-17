class AppConfig {
  static const coreApiBaseUrl = String.fromEnvironment(
    'CORE_API_BASE_URL',
    defaultValue: 'https://api.salaai.site',
  );
}
