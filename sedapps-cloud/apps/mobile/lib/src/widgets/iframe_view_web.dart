// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:ui_web' as ui_web;

import 'package:flutter/material.dart';

final Set<String> _registered = <String>{};

class IframeView extends StatelessWidget {
  const IframeView({required this.url, required this.viewId, super.key});

  final String url;
  final String viewId;

  @override
  Widget build(BuildContext context) {
    final fullViewId = '$viewId-${url.hashCode}';
    if (!_registered.contains(fullViewId)) {
      ui_web.platformViewRegistry.registerViewFactory(
        fullViewId,
        (int viewId) {
          final iframe = html.IFrameElement()
            ..src = url
            ..style.border = 'none'
            ..style.width = '100%'
            ..style.height = '100%'
            ..allowFullscreen = true;
          return iframe;
        },
      );
      _registered.add(fullViewId);
    }
    return HtmlElementView(viewType: fullViewId);
  }
}
