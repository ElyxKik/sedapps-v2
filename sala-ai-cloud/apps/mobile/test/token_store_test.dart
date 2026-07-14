import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sala_ai/src/data/token_store.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() => SharedPreferences.setMockInitialValues({}));

  test('TokenStore persists and clears a session', () async {
    final store = TokenStore();
    expect(await store.hasSession(), isFalse);

    await store.save(accessToken: 'access', refreshToken: 'refresh');
    expect(await store.accessToken(), 'access');
    expect(await store.refreshToken(), 'refresh');
    expect(await store.hasSession(), isTrue);

    await store.clear();
    expect(await store.accessToken(), isNull);
    expect(await store.refreshToken(), isNull);
    expect(await store.hasSession(), isFalse);
  });
}
