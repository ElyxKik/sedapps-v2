import 'package:dio/dio.dart';

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode, this.code});

  final String message;
  final int? statusCode;
  final String? code;

  factory ApiException.fromDio(DioException error) {
    final data = error.response?.data;
    String? detail;
    if (data is Map) {
      detail = data['detail']?.toString() ?? data['message']?.toString();
    }
    return ApiException(
      detail ?? _fallback(error.type),
      statusCode: error.response?.statusCode,
      code: data is Map ? data['code']?.toString() : null,
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
