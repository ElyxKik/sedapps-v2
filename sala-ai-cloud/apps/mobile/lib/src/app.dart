import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/theme.dart';
import 'data/theme_provider.dart';
import 'features/account/account_page.dart';
import 'features/auth/login_page.dart';
import 'features/auth/auth_session.dart';
import 'features/auth/session_loading_page.dart';
import 'features/cms/cms_page.dart';
import 'features/dashboard/dashboard_page.dart';
import 'features/onboarding/onboarding_page.dart';
import 'features/projects/project_detail_page.dart';
import 'features/projects/projects_page.dart';
import 'layout/app_shell.dart';

class SalaAIApp extends ConsumerWidget {
  const SalaAIApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeProvider);
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'Sala AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: themeMode,
      routerConfig: router,
    );
  }
}

final routerProvider = Provider<GoRouter>((ref) {
  final router = GoRouter(
    initialLocation: '/session',
    redirect: (context, state) {
      final auth = ref.read(authSessionProvider);
      final onLogin = state.matchedLocation == '/login';
      final onSession = state.matchedLocation == '/session';
      if (auth == AuthStatus.loading) {
        if (onSession) return null;
        final from = Uri.encodeComponent(state.uri.toString());
        return '/session?from=$from';
      }
      if (auth == AuthStatus.unauthenticated) return onLogin ? null : '/login';
      if (auth == AuthStatus.authenticated && onSession) {
        final from = state.uri.queryParameters['from'];
        if (from != null &&
            from.startsWith('/') &&
            !from.startsWith('//') &&
            from != '/login' &&
            !from.startsWith('/session')) {
          return from;
        }
        return '/';
      }
      if (auth == AuthStatus.authenticated && onLogin) return '/';
      return null;
    },
    routes: [
      GoRoute(
          path: '/session',
          builder: (context, state) => const SessionLoadingPage()),
      GoRoute(path: '/login', builder: (context, state) => const LoginPage()),
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          GoRoute(
              path: '/', builder: (context, state) => const DashboardPage()),
          GoRoute(
              path: '/projects',
              builder: (context, state) => const ProjectsPage()),
          GoRoute(
            path: '/projects/:id',
            builder: (context, state) =>
                ProjectDetailPage(projectId: state.pathParameters['id']!),
          ),
          GoRoute(
              path: '/new-site',
              builder: (context, state) => const OnboardingPage()),
          GoRoute(path: '/cms', builder: (context, state) => const CmsPage()),
          GoRoute(
              path: '/account',
              builder: (context, state) => const AccountPage()),
        ],
      ),
    ],
  );
  ref.listen(authSessionProvider, (_, __) => router.refresh());
  ref.onDispose(router.dispose);
  return router;
});
