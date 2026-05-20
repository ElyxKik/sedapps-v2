import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme.dart';
import '../../data/api_client.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final email = TextEditingController(text: 'test@seda.app');
  final password = TextEditingController(text: 'password123');
  final fullName = TextEditingController();
  final orgName = TextEditingController();
  bool loading = false;
  bool registering = false;
  bool _obscure = true;

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 900;
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: wide
            ? Row(
                children: [
                  Expanded(child: _buildHero()),
                  Expanded(child: _buildForm(context)),
                ],
              )
            : SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: _buildForm(context),
                ),
              ),
      ),
    );
  }

  Widget _buildHero() {
    return Container(
      decoration: const BoxDecoration(gradient: AppColors.heroGradient),
      child: Stack(
        children: [
          Positioned(
            right: -50,
            top: -50,
            child: Icon(Icons.cloud, size: 320, color: Colors.white.withValues(alpha: 0.08)),
          ),
          Positioned(
            left: -30,
            bottom: -30,
            child: Icon(Icons.auto_awesome, size: 240, color: Colors.white.withValues(alpha: 0.08)),
          ),
          Padding(
            padding: const EdgeInsets.all(56),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: const Icon(Icons.bolt, color: Colors.white, size: 28),
                    ),
                    const SizedBox(width: 14),
                    const Text('SedApps Cloud',
                        style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
                  ],
                ),
                const Spacer(),
                const Text('Crée des sites web pros avec l\'IA.',
                    style: TextStyle(color: Colors.white, fontSize: 42, fontWeight: FontWeight.w800, height: 1.1)),
                const SizedBox(height: 16),
                Text('Designer, copywriter, SEO, dev : nos agents IA collaborent pour livrer ton site en quelques minutes.',
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 16, height: 1.5)),
                const SizedBox(height: 32),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: const [
                    _Feature(icon: Icons.flash_on, label: 'Génération rapide'),
                    _Feature(icon: Icons.devices, label: 'Responsive'),
                    _Feature(icon: Icons.cloud_done, label: 'Déploiement OVH'),
                  ],
                ),
                const Spacer(),
                Text('© 2025 SedApps Cloud',
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildForm(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 440),
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(registering ? 'Créer un compte' : 'Bon retour 👋', style: Theme.of(context).textTheme.headlineLarge),
              const SizedBox(height: 8),
              Text(registering ? 'Démarre ton espace SedApps en quelques secondes.' : 'Connecte-toi à ton espace SedApps.',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary)),
              const SizedBox(height: 32),
              if (registering) ...[
                Text('Nom complet', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 6),
                TextField(
                  controller: fullName,
                  decoration: const InputDecoration(
                    hintText: 'Ton nom',
                    prefixIcon: Icon(Icons.person_outline),
                  ),
                ),
                const SizedBox(height: 18),
                Text('Organisation', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 6),
                TextField(
                  controller: orgName,
                  decoration: const InputDecoration(
                    hintText: 'Nom de ton entreprise',
                    prefixIcon: Icon(Icons.business_outlined),
                  ),
                ),
                const SizedBox(height: 18),
              ],
              Text('Email', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 6),
              TextField(
                controller: email,
                decoration: const InputDecoration(
                  hintText: 'toi@sedapps.cloud',
                  prefixIcon: Icon(Icons.mail_outline),
                ),
              ),
              const SizedBox(height: 18),
              Text('Mot de passe', style: Theme.of(context).textTheme.titleSmall),
              const SizedBox(height: 6),
              TextField(
                controller: password,
                obscureText: _obscure,
                decoration: InputDecoration(
                  hintText: '••••••••',
                  prefixIcon: const Icon(Icons.lock_outline),
                  suffixIcon: IconButton(
                    icon: Icon(_obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(onPressed: () {}, child: const Text('Mot de passe oublié ?')),
              ),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: loading ? null : registering ? _register : _login,
                style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 18)),
                child: loading
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(registering ? 'Créer mon compte' : 'Se connecter', style: const TextStyle(fontSize: 16)),
              ),
              const SizedBox(height: 24),
              Row(
                children: const [
                  Expanded(child: Divider()),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: Text('ou continuer avec', style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                  ),
                  Expanded(child: Divider()),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.g_mobiledata, size: 24),
                      label: const Text('Google'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.apple, size: 20),
                      label: const Text('Apple'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              Center(
                child: TextButton(
                  onPressed: loading ? null : () => setState(() => registering = !registering),
                  child: Text(
                    registering ? 'Déjà un compte ? Se connecter' : 'Pas encore de compte ? Créer un compte',
                    style: const TextStyle(color: AppColors.skyBlue, fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _login() async {
    setState(() => loading = true);
    try {
      await ref.read(apiClientProvider).login(email.text, password.text);
      if (mounted) context.go('/');
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Connexion impossible')));
      }
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> _register() async {
    setState(() => loading = true);
    try {
      await ref.read(apiClientProvider).register(
            email.text,
            password.text,
            orgName.text.isEmpty ? 'SedApps' : orgName.text,
            fullName.text.isEmpty ? 'Utilisateur' : fullName.text,
          );
      if (mounted) context.go('/');
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Inscription impossible')));
      }
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }
}

class _Feature extends StatelessWidget {
  const _Feature({required this.icon, required this.label});
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: Colors.white.withValues(alpha: 0.2)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: Colors.white, size: 16),
          const SizedBox(width: 8),
          Text(label, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
