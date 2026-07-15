import 'package:dio/dio.dart';

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode, this.code});

  final String message;
  final int? statusCode;
  final String? code;

  factory ApiException.fromDio(DioException error) {
    final data = error.response?.data;
    String? detail;
    String? code;
    if (data is Map) {
      final rawDetail = data['detail'];
      if (rawDetail is Map) {
        code = rawDetail['code']?.toString();
        if (code == 'insufficient_ai_credits') {
          final required = rawDetail['required_credits'] ?? 0;
          final available = rawDetail['available_credits'] ?? 0;
          detail = 'Crédits IA insuffisants : $required requis, '
              '$available disponibles.';
        } else {
          detail = rawDetail['message']?.toString();
        }
      } else {
        detail = rawDetail?.toString();
      }
      detail ??= data['message']?.toString();
      code ??= data['code']?.toString();
    }
    return ApiException(
      detail ?? _fallback(error.type),
      statusCode: error.response?.statusCode,
      code: code,
    );
  }

  static String _fallback(DioExceptionType type) => switch (type) {
        DioExceptionType.connectionTimeout ||
        DioExceptionType.sendTimeout ||
        DioExceptionType.receiveTimeout =>
          'Le serveur met trop de temps à répondre.',
        DioExceptionType.connectionError => 'Impossible de joindre le serveur.',
        DioExceptionType.cancel => 'La requête a été annulée.',
        _ => 'Une erreur inattendue est survenue.',
      };

  @override
  String toString() => message;
}
