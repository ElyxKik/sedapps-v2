import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/config.dart';
import 'mock_data.dart';
import 'token_store.dart';

final tokenStoreProvider = Provider<TokenStore>((ref) => TokenStore());

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(ref.watch(tokenStoreProvider));
});

class ApiClient {
  ApiClient(this._tokenStore)
      : dio = Dio(BaseOptions(
            baseUrl: AppConfig.coreApiBaseUrl,
            connectTimeout: const Duration(seconds: 15))) {
    dio.interceptors
        .add(InterceptorsWrapper(onRequest: (options, handler) async {
      final token = await _tokenStore.accessToken();
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
      handler.next(options);
    }));
  }

  final TokenStore _tokenStore;
  final Dio dio;

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

  String previewUrl(String nonce, {bool edit = false}) {
    final base = dio.options.baseUrl.replaceAll(RegExp(r'/$'), '');
    return '$base/v1/p/$nonce/index.html${edit ? '?edit=1' : ''}';
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
      };
    }
    return (await dio.get('/v1/credits/wallet')).data
        as Map<String, dynamic>;
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
    final estimate = await creditEstimate();
    if (estimate['can_start'] != true) {
      throw Exception(
          "Crédits insuffisants : ${estimate['estimated_credits']} crédits requis, ${estimate['available_credits']} disponibles.");
    }
    return (await dio.post('/v1/projects/$projectId/generate',
            data: {'force': true, 'locale': 'fr'}))
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

  Future<Map<String, dynamic>> deploySite(String projectId) async {
    if (useMockData) {
      return {
        'deployment_id': 'deploy-${DateTime.now().millisecondsSinceEpoch}',
        'status': 'pending'
      };
    }
    return (await dio.post('/v1/projects/$projectId/deploy', data: {})).data
        as Map<String, dynamic>;
  }

  Future<String> projectDownloadUrl(String projectId) async {
    final token = await _tokenStore.accessToken();
    if (token == null) {
      throw StateError('Utilisateur non authentifié');
    }
    return '${dio.options.baseUrl}/v1/projects/$projectId/download?token=${Uri.encodeComponent(token)}';
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
      'markdown': markdown,
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
      if (markdown != null) 'markdown': markdown,
      if (status != null) 'status': status,
    }))
        .data as Map<String, dynamic>;
  }

  Future<void> deleteArticle(String projectId, String articleId) async {
    await dio.delete('/v1/projects/$projectId/articles/$articleId');
  }
}
