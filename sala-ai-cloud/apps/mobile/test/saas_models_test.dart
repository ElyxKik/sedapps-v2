import 'package:flutter_test/flutter_test.dart';
import 'package:sala_ai/src/features/account/domain/credit_wallet.dart';
import 'package:sala_ai/src/features/publish/domain/deployment.dart';

void main() {
  group('CreditWallet', () {
    test('parses quota and computes a bounded usage ratio', () {
      final wallet = CreditWallet.fromJson({
        'balance_credits': 500,
        'reserved_credits': 25,
        'available_credits': 475,
        'used_this_month_credits': 125,
        'monthly_quota_credits': 500,
        'plan': 'starter',
      });

      expect(wallet.available, 475);
      expect(wallet.plan, 'starter');
      expect(wallet.usageRatio, 0.25);
    });

    test('supports an empty quota without division by zero', () {
      expect(CreditWallet.fromJson({}).usageRatio, 0);
    });
  });

  group('Deployment', () {
    test('accepts both deployment id contracts', () {
      final deployment = Deployment.fromJson({
        'deployment_id': 'deploy-1',
        'status': 'success',
        'url': 'https://site.example',
      });
      expect(deployment.id, 'deploy-1');
      expect(deployment.isSuccessful, isTrue);
    });

    test('exposes terminal failure states', () {
      final deployment = Deployment.fromJson({
        'id': 'deploy-1',
        'status': 'failed',
        'error': 'upload failed',
      });
      expect(deployment.isFailed, isTrue);
      expect(deployment.error, 'upload failed');
    });

    test('rejects a deployment without id', () {
      expect(
        () => Deployment.fromJson({'status': 'queued'}),
        throwsA(isA<FormatException>()),
      );
    });
  });
}
