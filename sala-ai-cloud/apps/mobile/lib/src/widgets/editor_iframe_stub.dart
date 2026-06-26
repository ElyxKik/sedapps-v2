import 'package:flutter/material.dart';

class EditorIframeController {
  void applyOps(String elementId, List<Map<String, dynamic>> ops) {}
  void reload() {}
  void dispose() {}
}

class EditorIframe extends StatelessWidget {
  const EditorIframe({
    required this.url,
    required this.onSelect,
    required this.controller,
    super.key,
  });

  final String url;
  final void Function(Map<String, dynamic> info) onSelect;
  final EditorIframeController controller;

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Text(
          'Éditeur visuel disponible uniquement sur la version web (Chrome).',
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
