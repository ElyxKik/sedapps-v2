import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/api_client.dart';
import '../../widgets/editor_iframe.dart';
import '../../widgets/notifications.dart';
import '../../widgets/page_scaffold.dart';
import '../projects/project_workspace_state.dart';

class EditorPage extends ConsumerStatefulWidget {
  const EditorPage({super.key});

  @override
  ConsumerState<EditorPage> createState() => _EditorPageState();
}

class _EditorPageState extends ConsumerState<EditorPage> {
  final EditorIframeController _ctrl = EditorIframeController();
  Map<String, dynamic>? _selected;
  bool _busy = false;
  int _undoDepth = 0;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _onSelect(Map<String, dynamic> info) {
    setState(() => _selected = info);
  }

  Future<void> _applyOps(List<Map<String, dynamic>> ops) async {
    final id = _selected?['id'] as String?;
    final projectId = ref.read(currentProjectIdProvider);
    if (id == null || projectId == null) return;
    setState(() => _busy = true);
    try {
      // optimistic UI in iframe
      _ctrl.applyOps(id, ops);
      final res = await ref.read(apiClientProvider).patchElement(projectId, id, ops);
      _undoDepth = (res['undo_depth'] as int?) ?? (_undoDepth + 1);
      if (mounted) NotificationService.success(context, 'Modification enregistrée');
    } catch (e) {
      if (mounted) NotificationService.error(context, 'Échec: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _askAi(String instruction) async {
    final id = _selected?['id'] as String?;
    final projectId = ref.read(currentProjectIdProvider);
    if (id == null || projectId == null || instruction.trim().isEmpty) return;
    setState(() => _busy = true);
    try {
      final res = await ref.read(apiClientProvider).editChat(projectId, id, instruction, _selected ?? {});
      final ops = ((res['ops'] as List?) ?? []).cast<Map<String, dynamic>>();
      if (ops.isNotEmpty) _ctrl.applyOps(id, ops);
      _undoDepth = (res['undo_depth'] as int?) ?? _undoDepth;
      if (mounted) NotificationService.success(context, 'IA : ${ops.length} modification(s) appliquée(s)');
    } catch (e) {
      if (mounted) NotificationService.error(context, 'IA échouée: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _undo() async {
    final projectId = ref.read(currentProjectIdProvider);
    if (projectId == null || _undoDepth <= 0) return;
    setState(() => _busy = true);
    try {
      final res = await ref.read(apiClientProvider).undoEdit(projectId);
      _undoDepth = (res['undo_depth'] as int?) ?? 0;
      _ctrl.reload();
      if (mounted) NotificationService.success(context, 'Modification annulée');
    } catch (e) {
      if (mounted) NotificationService.error(context, 'Annulation échouée: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final nonce = ref.watch(projectWorkspaceProvider.select((s) => s.previewNonce));
    final api = ref.read(apiClientProvider);

    return PageScaffold(
      title: 'Éditeur visuel',
      action: Row(mainAxisSize: MainAxisSize.min, children: [
        IconButton(
          tooltip: _undoDepth > 0 ? 'Annuler ($_undoDepth)' : 'Rien à annuler',
          onPressed: _undoDepth > 0 && !_busy ? _undo : null,
          icon: const Icon(Icons.undo),
        ),
        IconButton(
          tooltip: 'Recharger',
          onPressed: _ctrl.reload,
          icon: const Icon(Icons.refresh),
        ),
      ]),
      children: [
        if (nonce == null)
          const Padding(
            padding: EdgeInsets.all(24),
            child: Text('Aucun aperçu disponible. Génère d’abord ton site.'),
          )
        else
          SizedBox(
            height: MediaQuery.of(context).size.height - 180,
            child: LayoutBuilder(
              builder: (ctx, c) {
                final wide = c.maxWidth > 900;
                final hasSelection = _selected != null;
                final preview = Card(
                  clipBehavior: Clip.antiAlias,
                  child: EditorIframe(
                    url: api.previewUrl(nonce, edit: true),
                    controller: _ctrl,
                    onSelect: _onSelect,
                  ),
                );
                final panel = _PropertiesPanel(
                  selected: _selected,
                  busy: _busy,
                  onApplyOps: _applyOps,
                  onAskAi: _askAi,
                  onClose: () => setState(() => _selected = null),
                );
                if (!wide) {
                  return Stack(children: [
                    Positioned.fill(child: preview),
                    if (hasSelection)
                      Positioned(
                        right: 0, top: 0, bottom: 0,
                        width: c.maxWidth.clamp(280, 380).toDouble(),
                        child: Material(elevation: 4, child: panel),
                      ),
                  ]);
                }
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Expanded(child: preview),
                    if (hasSelection) ...[
                      const SizedBox(width: 12),
                      SizedBox(width: 360, child: panel),
                    ],
                  ],
                );
              },
            ),
          ),
      ],
    );
  }
}

class _ChatBar extends StatefulWidget {
  const _ChatBar({required this.enabled, required this.hint, required this.onSend});
  final bool enabled;
  final String hint;
  final void Function(String) onSend;

  @override
  State<_ChatBar> createState() => _ChatBarState();
}

class _ChatBarState extends State<_ChatBar> {
  final _ctrl = TextEditingController();
  final _focus = FocusNode();
  bool _focused = false;

  @override
  void initState() {
    super.initState();
    _ctrl.addListener(_onCtrl);
    _focus.addListener(_onFocus);
  }

  void _onCtrl() {
    if (mounted) setState(() {});
  }

  void _onFocus() {
    if (!mounted) return;
    setState(() => _focused = _focus.hasFocus);
  }

  @override
  void dispose() {
    _ctrl.removeListener(_onCtrl);
    _focus.removeListener(_onFocus);
    _ctrl.dispose();
    _focus.dispose();
    super.dispose();
  }

  void _send() {
    final v = _ctrl.text.trim();
    if (v.isEmpty || !widget.enabled) return;
    widget.onSend(v);
    _ctrl.clear();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasText = _ctrl.text.trim().isNotEmpty;
    final canSend = widget.enabled && hasText;
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 10, 12, 14),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(top: BorderSide(color: theme.dividerColor.withOpacity(0.6))),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 150),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceVariant.withOpacity(0.4),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: _focused
                    ? theme.colorScheme.primary.withOpacity(0.5)
                    : theme.dividerColor.withOpacity(0.4),
                width: 1.2,
              ),
              boxShadow: _focused
                  ? [BoxShadow(color: theme.colorScheme.primary.withOpacity(0.08), blurRadius: 14, offset: const Offset(0, 4))]
                  : const [],
            ),
            padding: const EdgeInsets.fromLTRB(16, 6, 6, 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: TextField(
                    controller: _ctrl,
                    focusNode: _focus,
                    enabled: widget.enabled,
                    minLines: 1,
                    maxLines: 5,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _send(),
                    style: theme.textTheme.bodyMedium,
                    decoration: InputDecoration(
                      hintText: widget.hint,
                      hintStyle: TextStyle(color: theme.hintColor),
                      isDense: true,
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(vertical: 10),
                    ),
                  ),
                ),
                const SizedBox(width: 6),
                Material(
                  color: canSend ? theme.colorScheme.primary : theme.colorScheme.outlineVariant,
                  shape: const CircleBorder(),
                  child: InkWell(
                    customBorder: const CircleBorder(),
                    onTap: canSend ? _send : null,
                    child: SizedBox(
                      width: 36,
                      height: 36,
                      child: Icon(
                        Icons.arrow_upward_rounded,
                        size: 20,
                        color: canSend ? theme.colorScheme.onPrimary : theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Icon(Icons.auto_awesome, size: 12, color: theme.hintColor),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'L’IA modifie uniquement l’élément sélectionné. Annulable à tout moment.',
                  style: theme.textTheme.labelSmall?.copyWith(color: theme.hintColor),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _PropertiesPanel extends StatelessWidget {
  const _PropertiesPanel({
    required this.selected,
    required this.busy,
    required this.onApplyOps,
    required this.onAskAi,
    required this.onClose,
  });
  final Map<String, dynamic>? selected;
  final bool busy;
  final void Function(List<Map<String, dynamic>>) onApplyOps;
  final void Function(String) onAskAi;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    if (selected == null) return const SizedBox.shrink();

    final tag = (selected!['tag'] ?? '').toString();
    final id = (selected!['id'] ?? '').toString();
    final text = (selected!['text'] ?? '').toString();
    final src = (selected!['src'] ?? '').toString();
    final href = (selected!['href'] ?? '').toString();

    final isText = const {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'a', 'button', 'li', 'label', 'blockquote'}.contains(tag);
    final isImg = tag == 'img';
    final isInput = tag == 'input' || tag == 'textarea';
    final isContainer = const {'section', 'div', 'header', 'footer', 'main', 'article', 'aside', 'nav', 'form'}.contains(tag);
    final showTextField = isText || isContainer;

    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          // Header with tag + close
          Container(
            padding: const EdgeInsets.fromLTRB(12, 8, 4, 8),
            decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Theme.of(context).dividerColor))),
            child: Row(children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(color: const Color(0xFFEDE9FE), borderRadius: BorderRadius.circular(6)),
                child: Text('<$tag>', style: const TextStyle(color: Color(0xFF7C3AED), fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 8),
              Expanded(child: Text(id, style: Theme.of(context).textTheme.bodySmall, overflow: TextOverflow.ellipsis)),
              if (busy) const Padding(padding: EdgeInsets.only(right: 8), child: SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))),
              IconButton(tooltip: 'Fermer', onPressed: onClose, icon: const Icon(Icons.close)),
            ]),
          ),
          // Properties (scrollable)
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (showTextField) ...[
                  Text(isContainer ? 'Texte (remplace le contenu)' : 'Texte', style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  _TextEditor(
                    initial: text,
                    onSave: (v) => onApplyOps([{'op': 'set_text', 'value': v}]),
                  ),
                  const SizedBox(height: 16),
                ],
                if (isImg) ...[
                  Text('Image', style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  _AttrEditor(label: 'URL image', initial: src, onSave: (v) => onApplyOps([{'op': 'set_attr', 'name': 'src', 'value': v}])),
                  const SizedBox(height: 8),
                  _AttrEditor(label: 'Texte alt', initial: (selected!['alt'] ?? '').toString(), onSave: (v) => onApplyOps([{'op': 'set_attr', 'name': 'alt', 'value': v}])),
                  const SizedBox(height: 16),
                ],
                if (tag == 'a') ...[
                  _AttrEditor(label: 'Lien (href)', initial: href, onSave: (v) => onApplyOps([{'op': 'set_attr', 'name': 'href', 'value': v}])),
                  const SizedBox(height: 16),
                ],
                if (isInput) ...[
                  Text('Champ', style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  _AttrEditor(label: 'Placeholder', initial: '', onSave: (v) => onApplyOps([{'op': 'set_attr', 'name': 'placeholder', 'value': v}])),
                  const SizedBox(height: 8),
                  _AttrEditor(label: 'Type', initial: '', onSave: (v) => onApplyOps([{'op': 'set_attr', 'name': 'type', 'value': v}])),
                  const SizedBox(height: 16),
                ],
                Text('Apparence', style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 8),
                _ColorRow(label: 'Fond', onPick: (c) => onApplyOps([{'op': 'set_style', 'name': 'background-color', 'value': c}])),
                const SizedBox(height: 8),
                _ColorRow(label: 'Texte', onPick: (c) => onApplyOps([{'op': 'set_style', 'name': 'color', 'value': c}])),
                if (isContainer) ...[
                  const SizedBox(height: 12),
                  Wrap(spacing: 8, runSpacing: 8, children: [
                    OutlinedButton(onPressed: () => onApplyOps([{'op': 'set_style', 'name': 'padding', 'value': '24px'}]), child: const Text('Padding 24')),
                    OutlinedButton(onPressed: () => onApplyOps([{'op': 'set_style', 'name': 'padding', 'value': '48px'}]), child: const Text('Padding 48')),
                    OutlinedButton(onPressed: () => onApplyOps([{'op': 'set_style', 'name': 'border-radius', 'value': '16px'}]), child: const Text('Radius 16')),
                  ]),
                ],
              ],
            ),
          ),
          // Chat bar at bottom of panel
          _ChatBar(
            enabled: !busy,
            hint: 'Demande à l’IA pour cet élément…',
            onSend: onAskAi,
          ),
        ],
      ),
    );
  }
}

class _TextEditor extends StatefulWidget {
  const _TextEditor({required this.initial, required this.onSave});
  final String initial;
  final void Function(String) onSave;

  @override
  State<_TextEditor> createState() => _TextEditorState();
}

class _TextEditorState extends State<_TextEditor> {
  late final TextEditingController _ctrl = TextEditingController(text: widget.initial);
  late String _baseline = widget.initial;

  @override
  void initState() {
    super.initState();
    _ctrl.addListener(_onChange);
  }

  void _onChange() => setState(() {});

  @override
  void didUpdateWidget(covariant _TextEditor oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initial != widget.initial) {
      _baseline = widget.initial;
      _ctrl.text = widget.initial;
    }
  }

  @override
  void dispose() {
    _ctrl.removeListener(_onChange);
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dirty = _ctrl.text != _baseline;
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      TextField(
        controller: _ctrl,
        maxLines: 5,
        minLines: 2,
        decoration: const InputDecoration(labelText: 'Texte', border: OutlineInputBorder()),
      ),
      const SizedBox(height: 8),
      FilledButton.icon(
        onPressed: dirty
            ? () {
                widget.onSave(_ctrl.text);
                setState(() => _baseline = _ctrl.text);
              }
            : null,
        icon: const Icon(Icons.save, size: 16),
        label: Text(dirty ? 'Enregistrer' : 'Aucun changement'),
      ),
    ]);
  }
}

class _AttrEditor extends StatefulWidget {
  const _AttrEditor({required this.label, required this.initial, required this.onSave});
  final String label;
  final String initial;
  final void Function(String) onSave;

  @override
  State<_AttrEditor> createState() => _AttrEditorState();
}

class _AttrEditorState extends State<_AttrEditor> {
  late final TextEditingController _ctrl = TextEditingController(text: widget.initial);

  @override
  void didUpdateWidget(covariant _AttrEditor oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initial != widget.initial) _ctrl.text = widget.initial;
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Expanded(
        child: TextField(
          controller: _ctrl,
          decoration: InputDecoration(labelText: widget.label, border: const OutlineInputBorder(), isDense: true),
          onSubmitted: widget.onSave,
        ),
      ),
      const SizedBox(width: 8),
      IconButton(onPressed: () => widget.onSave(_ctrl.text), icon: const Icon(Icons.check)),
    ]);
  }
}

class _ColorRow extends StatelessWidget {
  const _ColorRow({required this.label, required this.onPick});
  final String label;
  final void Function(String) onPick;

  static const _colors = [
    '#0EA5E9', '#2563EB', '#7C3AED', '#EC4899', '#EF4444',
    '#F59E0B', '#10B981', '#111827', '#FFFFFF', 'transparent',
  ];

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      SizedBox(width: 60, child: Text(label)),
      Expanded(
        child: Wrap(
          spacing: 6,
          runSpacing: 6,
          children: _colors.map((c) {
            final isTransparent = c == 'transparent';
            return InkWell(
              onTap: () => onPick(c),
              child: Container(
                width: 24,
                height: 24,
                decoration: BoxDecoration(
                  color: isTransparent ? Colors.white : Color(int.parse(c.replaceFirst('#', '0xFF'))),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: Colors.black26),
                ),
                child: isTransparent ? const Icon(Icons.block, size: 14, color: Colors.black45) : null,
              ),
            );
          }).toList(),
        ),
      ),
    ]);
  }
}
