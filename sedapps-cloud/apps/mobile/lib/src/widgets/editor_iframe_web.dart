// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:js_util' as js_util;
import 'dart:ui_web' as ui_web;

import 'package:flutter/material.dart';

final Set<String> _registered = <String>{};
final Map<String, html.IFrameElement> _iframes = {};

class EditorIframeController {
  String? _viewId;

  void _attach(String viewId) {
    _viewId = viewId;
  }

  void applyOps(String elementId, List<Map<String, dynamic>> ops) {
    final iframe = _viewId == null ? null : _iframes[_viewId];
    final win = iframe?.contentWindow;
    if (win == null) return;
    final payload = js_util.jsify({'type': 'sed:apply', 'id': elementId, 'ops': ops});
    js_util.callMethod(win, 'postMessage', [payload, '*']);
  }

  void reload() {
    final iframe = _viewId == null ? null : _iframes[_viewId];
    if (iframe == null) return;
    final src = iframe.src;
    iframe.src = '';
    iframe.src = src;
  }

  void dispose() {}
}

class EditorIframe extends StatefulWidget {
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
  State<EditorIframe> createState() => _EditorIframeState();
}

class _EditorIframeState extends State<EditorIframe> {
  late final String _viewId;
  late final void Function(html.Event) _listener;

  @override
  void initState() {
    super.initState();
    _viewId = 'sed-editor-${widget.url.hashCode}-${DateTime.now().microsecondsSinceEpoch}';
    if (!_registered.contains(_viewId)) {
      ui_web.platformViewRegistry.registerViewFactory(_viewId, (int _) {
        final iframe = html.IFrameElement()
          ..src = widget.url
          ..style.border = 'none'
          ..style.width = '100%'
          ..style.height = '100%';
        _iframes[_viewId] = iframe;
        return iframe;
      });
      _registered.add(_viewId);
    }
    widget.controller._attach(_viewId);
    _listener = (html.Event ev) {
      final me = ev as html.MessageEvent;
      // Cross-origin postMessage: data may be a JS object, convert to Dart.
      final raw = me.data;
      final data = raw is Map ? raw : js_util.dartify(raw);
      if (data is! Map) return;
      final type = data['type'];
      if (type == 'sed:select') {
        widget.onSelect(Map<String, dynamic>.from(data));
      }
    };
    html.window.addEventListener('message', _listener);
  }

  @override
  void dispose() {
    html.window.removeEventListener('message', _listener);
    _iframes.remove(_viewId);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => HtmlElementView(viewType: _viewId);
}
