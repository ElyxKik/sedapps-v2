import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/theme.dart';
import 'data/theme_provider.dart';
import 'features/account/account_page.dart';
import 'features/auth/login_page.dart';
import 'features/cms/cms_hub_page.dart';
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
    return MaterialApp.router(
      title: 'Sala AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: themeMode,
      routerConfig: _router,
    );
  }
}

final _router = GoRouter(
  initialLocation: '/login',
  routes: [
    GoRoute(path: '/login', builder: (context, state) => const LoginPage()),
    ShellRoute(
      builder: (context, state, child) => AppShell(child: child),
      routes: [
        GoRoute(path: '/', builder: (context, state) => const DashboardPage()),
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
        GoRoute(path: '/cms', builder: (context, state) => const CmsHubPage()),
        GoRoute(
            path: '/account', builder: (context, state) => const AccountPage()),
      ],
    ),
  ],
);
