import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class IframeView extends StatelessWidget {
  const IframeView({required this.url, required this.viewId, super.key});

  final String url;
  final String viewId;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.open_in_browser, size: 48, color: Colors.black45),
            const SizedBox(height: 16),
            const Text(
              'Aperçu disponible dans le navigateur',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Text(
              url,
              style: const TextStyle(fontSize: 12, color: Colors.black45),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: () => launchUrl(Uri.parse(url)),
              icon: const Icon(Icons.open_in_new),
              label: const Text('Ouvrir le site'),
            ),
          ],
        ),
      ),
    );
  }
}
