import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/config.dart';
import '../../core/theme.dart';
import '../../widgets/iframe_view.dart';
import '../../widgets/notifications.dart';
import '../projects/project_workspace_state.dart';

enum PreviewDevice { desktop, tablet, mobile }

class PreviewPage extends ConsumerStatefulWidget {
  const PreviewPage({super.key});

  @override
  ConsumerState<PreviewPage> createState() => _PreviewPageState();
}

class _PreviewPageState extends ConsumerState<PreviewPage> {
  PreviewDevice _device = PreviewDevice.desktop;
  int _refreshKey = 0;

  double get _deviceWidth {
    switch (_device) {
      case PreviewDevice.desktop:
        return 1200;
      case PreviewDevice.tablet:
        return 768;
      case PreviewDevice.mobile:
        return 390;
    }
  }

  String? _previewUrl(String? nonce) {
    if (nonce == null || nonce.isEmpty) return null;
    return '${AppConfig.coreApiBaseUrl}/v1/p/$nonce/index.html';
  }

  @override
  Widget build(BuildContext context) {
    final workspace = ref.watch(projectWorkspaceProvider);
    final url = _previewUrl(workspace.previewNonce);

    return Container(
      color: AppColors.background,
      child: Column(
        children: [
          _Toolbar(
            device: _device,
            onDeviceChange: (d) => setState(() => _device = d),
            url: url ?? 'https://${workspace.publish.domain}',
            onOpen: () async {
              if (url == null) return;
              await launchUrl(Uri.parse(url));
            },
            onRefresh: () {
              setState(() => _refreshKey++);
              NotificationService.success(context, 'Aperçu rafraîchi');
            },
          ),
          Expanded(
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 350),
                  curve: Curves.easeOutCubic,
                  width: _deviceWidth,
                  height: double.infinity,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppColors.border),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.06),
                        blurRadius: 24,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: url == null
                      ? const _NoPreview()
                      : IframeView(
                          key: ValueKey('iframe-$_refreshKey'),
                          url: url,
                          viewId: 'preview',
                        ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _NoPreview extends StatelessWidget {
  const _NoPreview();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.auto_awesome_outlined, size: 48, color: Colors.black38),
            SizedBox(height: 12),
            Text('Aperçu indisponible',
                style: TextStyle(fontWeight: FontWeight.w700)),
            SizedBox(height: 6),
            Text(
              'Lance la génération depuis l\'onboarding pour voir ton site ici.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.black54),
            ),
          ],
        ),
      ),
    );
  }
}

class _Toolbar extends StatelessWidget {
  const _Toolbar({
    required this.device,
    required this.onDeviceChange,
    required this.url,
    required this.onOpen,
    required this.onRefresh,
  });

  final PreviewDevice device;
  final ValueChanged<PreviewDevice> onDeviceChange;
  final String url;
  final VoidCallback onOpen;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(bottom: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          SegmentedButton<PreviewDevice>(
            segments: const [
              ButtonSegment(
                  value: PreviewDevice.desktop,
                  icon: Icon(Icons.desktop_mac),
                  label: Text('Desktop')),
              ButtonSegment(
                  value: PreviewDevice.tablet,
                  icon: Icon(Icons.tablet_mac),
                  label: Text('Tablet')),
              ButtonSegment(
                  value: PreviewDevice.mobile,
                  icon: Icon(Icons.phone_iphone),
                  label: Text('Mobile')),
            ],
            selected: {device},
            onSelectionChanged: (s) => onDeviceChange(s.first),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: AppColors.background,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  const Icon(Icons.lock_outline,
                      size: 14, color: AppColors.textSecondary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      url,
                      style: const TextStyle(
                          fontSize: 13, color: AppColors.textSecondary),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 12),
          IconButton(
              onPressed: onRefresh,
              icon: const Icon(Icons.refresh),
              tooltip: 'Rafraîchir'),
          IconButton(
              onPressed: onOpen,
              icon: const Icon(Icons.open_in_new),
              tooltip: 'Ouvrir'),
        ],
      ),
    );
  }
}
