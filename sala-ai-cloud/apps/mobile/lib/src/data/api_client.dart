import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/config.dart';
import '../core/api_exception.dart';
import '../features/auth/auth_session.dart';
import 'mock_data.dart';
import 'token_store.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(
    ref.watch(tokenStoreProvider),
    onSessionExpired: () => ref.read(authSessionProvider.notifier).expired(),
  );
});

class ApiClient {
  ApiClient(this._tokenStore, {required this.onSessionExpired})
      : dio = Dio(BaseOptions(
            baseUrl: AppConfig.coreApiBaseUrl,
            connectTimeout: const Duration(seconds: 15))) {
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _tokenStore.accessToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        final request = error.requestOptions;
        final canRefresh = error.response?.statusCode == 401 &&
            request.path != '/v1/auth/refresh' &&
            request.extra['retried'] != true;
        if (canRefresh && await _refreshAccessToken()) {
          try {
            request.extra['retried'] = true;
            request.headers['Authorization'] =
                'Bearer ${await _tokenStore.accessToken()}';
            return handler.resolve(await dio.fetch(request));
          } on DioException catch (retryError) {
            return handler.reject(retryError);
          }
        }
        if (error.response?.statusCode == 401) {
          await _tokenStore.clear();
          onSessionExpired();
        }
        handler.reject(DioException(
          requestOptions: request,
          response: error.response,
          type: error.type,
          error: ApiException.fromDio(error),
          message: ApiException.fromDio(error).message,
        ));
      },
    ));
  }

  final TokenStore _tokenStore;
  final void Function() onSessionExpired;
  final Dio dio;
  Future<bool>? _refreshing;

  Future<bool> _refreshAccessToken() {
    return _refreshing ??=
        _performRefresh().whenComplete(() => _refreshing = null);
  }

  Future<bool> _performRefresh() async {
    final token = await _tokenStore.refreshToken();
    if (token == null) return false;
    try {
      final response =
          await Dio(BaseOptions(baseUrl: dio.options.baseUrl)).post(
        '/v1/auth/refresh',
        data: {'refresh_token': token},
      );
      await _tokenStore.save(
        accessToken: response.data['access_token'] as String,
        refreshToken: response.data['refresh_token'] as String,
      );
      return true;
    } on DioException {
      return false;
    }
  }

  Future<void> login(String email, String password) async {
    if (useMockData) {
      await _tokenStore.save(
        accessToken: 'mock-token-${DateTime.now().millisecondsSinceEpoch}',
        refreshToken: 'mock-refresh-token',
      );
      return;
    }
    final response = await dio
        .post('/v1/auth/login', data: {'email': email, 'password': password});
    await _tokenStore.save(
      accessToken: response.data['access_token'] as String,
      refreshToken: response.data['refresh_token'] as String,
    );
  }

  Future<void> register(
      String email, String password, String orgName, String fullName) async {
    final response = await dio.post('/v1/auth/register', data: {
      'email': email,
      'password': password,
      'org_name': orgName,
      'full_name': fullName,
    });
    await _tokenStore.save(
      accessToken: response.data['access_token'] as String,
      refreshToken: response.data['refresh_token'] as String,
    );
  }

  Future<List<dynamic>> projects() async {
    if (useMockData) return mockProjects;
    return (await dio.get('/v1/projects')).data as List<dynamic>;
  }

  Future<Map<String, dynamic>> project(String projectId) async {
    return (await dio.get('/v1/projects/$projectId')).data
        as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateProject(
      String projectId, Map<String, dynamic> data) async {
    return (await dio.patch('/v1/projects/$projectId', data: data)).data
        as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> patchElement(String projectId, String elementId,
      List<Map<String, dynamic>> ops) async {
    final res = await dio.post('/v1/projects/$projectId/patch_element',
        data: {'element_id': elementId, 'ops': ops});
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> undoEdit(String projectId) async {
    final res = await dio.post('/v1/projects/$projectId/undo');
    return res.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> editChat(String projectId, String elementId,
      String instruction, Map<String, dynamic> selected) async {
    final res = await dio.post('/v1/projects/$projectId/edit_chat', data: {
      'element_id': elementId,
      'instruction': instruction,
      'selected': selected,
    });
    return res.data as Map<String, dynamic>;
  }

  String previewUrl(String nonce, {bool edit = false, String? page}) {
    final base = dio.options.baseUrl.replaceAll(RegExp(r'/$'), '');
    final params = <String, String>{
      if (edit) 'edit': '1',
      if (edit) 'structured': '1',
      if (page != null && page.isNotEmpty) 'page': page,
    };
    final query = params.entries
        .map((entry) => '${entry.key}=${Uri.encodeQueryComponent(entry.value)}')
        .join('&');
    return '$base/v1/p/$nonce/index.html${query.isEmpty ? '' : '?$query'}';
  }

  Future<Map<String, dynamic>> account() async {
    return (await dio.get('/v1/account')).data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> creditWallet() async {
    if (useMockData) {
      return {
        'balance_credits': 100,
        'reserved_credits': 0,
        'available_credits': 100,
        'used_this_month_credits': 0,
        'monthly_quota_credits': 100,
        'plan': 'free',
        'reset_at': null,
        'tokens_per_credit': 1000,
      };
    }
    return (await dio.get('/v1/credits/wallet')).data as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> billingPlans() async {
    if (useMockData) {
      return [
        {
          'id': '00000000-0000-0000-0000-000000000001',
          'slug': 'free',
          'name': 'Gratuit',
          'description': 'Pour découvrir Sala AI.',
          'billing_interval': 'month',
          'price_cents': 0,
          'currency': 'EUR',
          'monthly_credits': 50,
          'checkout_enabled': false,
        },
        {
          'id': '00000000-0000-0000-0000-000000000002',
          'slug': 'pro',
          'name': 'Pro',
          'description': 'Pour créer et publier plus rapidement.',
          'billing_interval': 'month',
          'price_cents': 2900,
          'currency': 'EUR',
          'monthly_credits': 1000,
          'checkout_enabled': true,
        },
      ];
    }
    final response = await dio.get('/v1/billing/plans');
    final data = response.data as Map<String, dynamic>;
    return (data['plans'] as List<dynamic>? ?? const [])
        .whereType<Map>()
        .map((plan) => Map<String, dynamic>.from(plan))
        .toList();
  }

  Future<Map<String, dynamic>> createBillingCheckout({
    required String planId,
    required String phoneNumber,
    required String countryCode,
    String? discountCode,
  }) async {
    final response = await dio.post('/v1/billing/checkout', data: {
      'planId': planId,
      'phoneNumber': phoneNumber,
      'countryCode': countryCode,
      if (discountCode != null && discountCode.trim().isNotEmpty)
        'discountCode': discountCode.trim(),
    });
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> creditEstimate(
      {String operation = 'site_generation', String tier = 'standard'}) async {
    if (useMockData) {
      return {
        'estimated_credits': 250,
        'max_credits': 500,
        'estimated_tokens': 250000,
        'max_tokens': 500000,
        'available_credits': 100,
        'can_start': false,
      };
    }
    return (await dio.post('/v1/credits/estimate',
            data: {'operation': operation, 'tier': tier}))
        .data as Map<String, dynamic>;
  }

  Future<void> updateAccount(Map<String, dynamic> data) async {
    if (useMockData) return;
    await dio.patch('/v1/account', data: data);
  }

  Future<void> deleteProject(String projectId) async {
    if (useMockData) return;
    await dio.delete('/v1/projects/$projectId');
  }

  Future<Map<String, dynamic>> createProject(
      String name, String? sector) async {
    if (useMockData) {
      return {
        'id': 'proj-${DateTime.now().millisecondsSinceEpoch}',
        'name': name,
        'sector': sector,
        'status': 'draft'
      };
    }
    return (await dio
            .post('/v1/projects', data: {'name': name, 'sector': sector}))
        .data as Map<String, dynamic>;
  }

  Future<void> saveOnboarding(
      String projectId, Map<String, dynamic> data) async {
    if (useMockData) return;
    await dio.post('/v1/projects/$projectId/onboarding', data: data);
  }

  Future<Map<String, dynamic>> generateSite(String projectId) async {
    if (useMockData) {
      return {
        'job_id': 'job-${DateTime.now().millisecondsSinceEpoch}',
        'status': 'queued'
      };
    }
    return (await dio.post('/v1/projects/$projectId/generate',
            data: {'force': false, 'locale': 'fr'}))
        .data as Map<String, dynamic>;
  }

  Future<String> chatWithProject(
      String projectId, List<Map<String, String>> messages) async {
    try {
      final response = await dio
          .post('/v1/projects/$projectId/chat', data: {'messages': messages});
      final data = response.data as Map<String, dynamic>;
      return (data['message'] ?? '').toString();
    } on DioException catch (e) {
      final data = e.response?.data;
      if (data is Map && data['detail'] != null) {
        throw Exception(data['detail'].toString());
      }
      throw Exception(e.message ?? 'Erreur API inconnue');
    }
  }

  Future<Map<String, dynamic>> getProjectPlan(String projectId) async {
    if (useMockData) {
      return {
        'title': 'Plan de création du site',
        'phases': [
          {
            'phase': 'Analyse & Design',
            'duration': '2-3 jours',
            'tasks': [
              {
                'id': 'task-1',
                'title': 'Analyse du brief',
                'status': 'pending',
                'priority': 'high'
              },
              {
                'id': 'task-2',
                'title': 'Création de la palette de couleurs',
                'status': 'pending',
                'priority': 'high'
              },
            ],
          },
        ],
        'timeline': '10-14 jours',
      };
    }
    return (await dio.get('/v1/projects/$projectId/plan')).data
        as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> job(String jobId) async {
    if (useMockData) return mockJob;
    return (await dio.get('/v1/jobs/$jobId')).data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> deploySite(String projectId,
      {String? customDomain}) async {
    if (useMockData) {
      return {
        'deployment_id': 'deploy-${DateTime.now().millisecondsSinceEpoch}',
        'status': 'pending'
      };
    }
    return (await dio.post('/v1/projects/$projectId/deploy', data: {
      if (customDomain != null && customDomain.isNotEmpty)
        'custom_domain': customDomain,
    }))
        .data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> deployment(
      String projectId, String deploymentId) async {
    return (await dio.get('/v1/projects/$projectId/deployments/$deploymentId'))
        .data as Map<String, dynamic>;
  }

  Future<List<dynamic>> domains() async {
    if (useMockData) return const [];
    return (await dio.get('/v1/domains')).data as List<dynamic>;
  }

  Future<Map<String, dynamic>> searchDomain(String name) async =>
      (await dio.get('/v1/domains/search', queryParameters: {'q': name})).data
          as Map<String, dynamic>;

  Future<Map<String, dynamic>> addDomain(String name,
          {DateTime? expiresAt}) async =>
      (await dio.post('/v1/domains', data: {
        'name': name,
        if (expiresAt != null)
          'expires_at': expiresAt.toUtc().toIso8601String(),
      }))
          .data as Map<String, dynamic>;

  Future<Map<String, dynamic>> addSubdomain(
          String parentId, String label) async =>
      (await dio
              .post('/v1/domains/$parentId/subdomains', data: {'label': label}))
          .data as Map<String, dynamic>;

  Future<Map<String, dynamic>> assignDomain(
          String domainId, String? projectId) async =>
      (await dio.patch('/v1/domains/$domainId/assignment',
              data: {'project_id': projectId}))
          .data as Map<String, dynamic>;

  Future<void> renewDomain(String domainId) async {
    await dio.post('/v1/domains/$domainId/renew');
  }

  Future<String> projectDownloadUrl(String projectId) async {
    final response = await dio.post('/v1/projects/$projectId/download-ticket');
    final path = response.data['path']?.toString();
    if (path == null || path.isEmpty) {
      throw const FormatException('Ticket de téléchargement invalide.');
    }
    final base = dio.options.baseUrl.replaceAll(RegExp(r'/$'), '');
    return path.startsWith('http') ? path : '$base$path';
  }

  Future<List<dynamic>> articles(String projectId) async {
    if (useMockData) return mockArticles;
    return (await dio.get('/v1/projects/$projectId/articles')).data
        as List<dynamic>;
  }

  Future<Map<String, dynamic>> createArticle(
      String projectId, String title, String markdown, String status) async {
    return (await dio.post('/v1/projects/$projectId/articles', data: {
      'title': title,
      'content_md': markdown,
      'status': status,
    }))
        .data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateArticle(
    String projectId,
    String articleId, {
    String? title,
    String? markdown,
    String? status,
  }) async {
    return (await dio
            .patch('/v1/projects/$projectId/articles/$articleId', data: {
      if (title != null) 'title': title,
      if (markdown != null) 'content_md': markdown,
      if (status != null) 'status': status,
    }))
        .data as Map<String, dynamic>;
  }

  Future<void> deleteArticle(String projectId, String articleId) async {
    await dio.delete('/v1/projects/$projectId/articles/$articleId');
  }

  Future<List<dynamic>> forms(String projectId) async {
    return (await dio.get('/v1/projects/$projectId/forms')).data
        as List<dynamic>;
  }

  Future<Map<String, dynamic>> createForm(
      String projectId, String name, Map<String, dynamic> schema) async {
    return (await dio.post('/v1/projects/$projectId/forms',
            data: {'name': name, 'schema': schema}))
        .data as Map<String, dynamic>;
  }

  Future<List<dynamic>> submissions(String projectId) async {
    return (await dio.get('/v1/projects/$projectId/submissions')).data
        as List<dynamic>;
  }

  Future<List<dynamic>> media(String projectId) async {
    return (await dio.get('/v1/projects/$projectId/media')).data
        as List<dynamic>;
  }

  Future<Map<String, dynamic>> projectDocument(String projectId) async {
    return (await dio.get('/v1/projects/$projectId/document')).data
        as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createPage(String projectId,
      {required String name,
      required String slug,
      String template = 'standard'}) async {
    return (await dio.post('/v1/projects/$projectId/pages', data: {
      'name': name,
      'slug': slug,
      'template': template,
    }))
        .data as Map<String, dynamic>;
  }

  Future<void> deletePage(String projectId, String pageId) async {
    await dio.delete('/v1/projects/$projectId/pages/$pageId');
  }

  Future<Map<String, dynamic>> createPageComponent(
      String projectId, String pageId, String type,
      {Map<String, dynamic> props = const {}}) async {
    return (await dio.post('/v1/projects/$projectId/pages/$pageId/components',
            data: {'type': type, 'props': props}))
        .data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> regeneratePage(
      String projectId, String pageId, String instruction) async {
    return (await dio.post('/v1/projects/$projectId/pages/$pageId/regenerate',
            data: {'instruction': instruction}))
        .data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> replaceProjectDocument(
      String projectId, Map<String, dynamic> document) async {
    return (await dio.put('/v1/projects/$projectId/document',
            data: {'document': document}))
        .data as Map<String, dynamic>;
  }

  Future<List<dynamic>> comments(String projectId) async {
    return (await dio.get('/v1/projects/$projectId/comments')).data
        as List<dynamic>;
  }

  Future<void> updateCommentStatus(
      String projectId, String commentId, String status) async {
    await dio.patch('/v1/projects/$projectId/comments/$commentId',
        data: {'status': status});
  }
}
