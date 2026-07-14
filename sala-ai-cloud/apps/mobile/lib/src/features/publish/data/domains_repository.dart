import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/api_client.dart';
import '../domain/managed_domain.dart';

final domainsRepositoryProvider = Provider<DomainsRepository>(
  (ref) => DomainsRepository(ref.watch(apiClientProvider)),
);

final managedDomainsProvider = FutureProvider<List<ManagedDomain>>(
  (ref) => ref.watch(domainsRepositoryProvider).list(),
);

class DomainsRepository {
  const DomainsRepository(this._api);
  final ApiClient _api;

  Future<List<ManagedDomain>> list() async => (await _api.domains())
      .map((item) => ManagedDomain.fromJson(item as Map<String, dynamic>))
      .toList();

  Future<DomainSearchResult> search(String name) async =>
      DomainSearchResult.fromJson(await _api.searchDomain(name));

  Future<ManagedDomain> add(String name, {DateTime? expiresAt}) async =>
      ManagedDomain.fromJson(await _api.addDomain(name, expiresAt: expiresAt));

  Future<ManagedDomain> addSubdomain(String parentId, String label) async =>
      ManagedDomain.fromJson(await _api.addSubdomain(parentId, label));

  Future<ManagedDomain> assign(String domainId, String? projectId) async =>
      ManagedDomain.fromJson(await _api.assignDomain(domainId, projectId));

  Future<void> renew(String domainId) => _api.renewDomain(domainId);
}
