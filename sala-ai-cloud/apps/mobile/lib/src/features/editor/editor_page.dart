import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/api_client.dart';
import '../../core/theme.dart';
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
  final TextEditingController _codeCtrl = TextEditingController();
  final TextEditingController _codeAiCtrl = TextEditingController();
  Map<String, dynamic>? _selected;
  Map<String, dynamic>? _document;
  String? _selectedPageId;
  _EditorMode _mode = _EditorMode.visual;
  _Viewport _viewport = _Viewport.desktop;
  bool _busy = false;
  bool _loading = true;
  int _undoDepth = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadDocument());
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _codeCtrl.dispose();
    _codeAiCtrl.dispose();
    super.dispose();
  }

  List<Map<String, dynamic>> get _pages =>
      ((_document?['pages'] as List?) ?? const [])
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();

  Map<String, dynamic>? get _selectedPage {
    for (final page in _pages) {
      if (page['id'] == _selectedPageId) return page;
    }
    return _pages.isEmpty ? null : _pages.first;
  }

  String get _selectedSlug =>
      _selectedPage?['props']?['slug']?.toString() ?? 'home';

  Future<void> _loadDocument() async {
    final projectId = ref.read(currentProjectIdProvider);
    if (projectId == null) return;
    try {
      final result =
          await ref.read(apiClientProvider).projectDocument(projectId);
      final document = Map<String, dynamic>.from(result['document'] as Map);
      if (!mounted) return;
      setState(() {
        _document = document;
        _selectedPageId ??=
            (document['pages'] as List?)?.firstOrNull?['id']?.toString();
        _undoDepth = (result['version'] as int? ?? 1) - 1;
        _codeCtrl.text = const JsonEncoder.withIndent('  ').convert(document);
        _loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
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
      final res =
          await ref.read(apiClientProvider).patchElement(projectId, id, ops);
      _undoDepth = (res['undo_depth'] as int?) ?? (_undoDepth + 1);
      if (mounted)
        NotificationService.success(context, 'Modification enregistrée');
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
      final res = await ref
          .read(apiClientProvider)
          .editChat(projectId, id, instruction, _selected ?? {});
      final ops = ((res['ops'] as List?) ?? []).cast<Map<String, dynamic>>();
      if (ops.isNotEmpty) _ctrl.applyOps(id, ops);
      _undoDepth = (res['undo_depth'] as int?) ?? _undoDepth;
      if (mounted)
        NotificationService.success(
            context, 'IA : ${ops.length} modification(s) appliquée(s)');
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
      await _loadDocument();
      if (mounted) NotificationService.success(context, 'Modification annulée');
    } catch (e) {
      if (mounted) NotificationService.error(context, 'Annulation échouée: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _createPage() async {
    final name = TextEditingController();
    final slug = TextEditingController();
    String template = 'standard';
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
          builder: (context, setDialogState) => AlertDialog(
                title: const Text('Nouvelle page'),
                content: SizedBox(
                    width: 460,
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                      TextField(
                          controller: name,
                          autofocus: true,
                          decoration: const InputDecoration(
                              labelText: 'Nom',
                              prefixIcon: Icon(Icons.description_outlined)),
                          onChanged: (value) => slug.text = _slugify(value)),
                      const SizedBox(height: 12),
                      TextField(
                          controller: slug,
                          decoration: const InputDecoration(
                              labelText: 'Adresse', prefixText: '/')),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                          initialValue: template,
                          decoration:
                              const InputDecoration(labelText: 'Modèle'),
                          items: const [
                            DropdownMenuItem(
                                value: 'standard',
                                child: Text('Page standard')),
                            DropdownMenuItem(
                                value: 'blank', child: Text('Page vierge')),
                            DropdownMenuItem(
                                value: 'contact', child: Text('Page contact')),
                          ],
                          onChanged: (value) => setDialogState(
                              () => template = value ?? template)),
                    ])),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(context, false),
                      child: const Text('Annuler')),
                  FilledButton(
                      onPressed: () => Navigator.pop(context, true),
                      child: const Text('Créer'))
                ],
              )),
    );
    if (accepted != true ||
        name.text.trim().isEmpty ||
        slug.text.trim().isEmpty) return;
    final projectId = ref.read(currentProjectIdProvider);
    if (projectId == null) return;
    setState(() => _busy = true);
    try {
      final result = await ref.read(apiClientProvider).createPage(projectId,
          name: name.text.trim(), slug: slug.text.trim(), template: template);
      _selectedPageId = result['page']?['id']?.toString();
      await _loadDocument();
      _ctrl.reload();
    } catch (error) {
      if (mounted)
        NotificationService.error(context, 'Création impossible : $error');
    } finally {
      name.dispose();
      slug.dispose();
      if (mounted) setState(() => _busy = false);
    }
  }

  String _slugify(String value) => value
      .toLowerCase()
      .trim()
      .replaceAll(RegExp(r'[^a-z0-9]+'), '-')
      .replaceAll(RegExp(r'^-|-$'), '');

  Future<void> _deletePage() async {
    final page = _selectedPage;
    final projectId = ref.read(currentProjectIdProvider);
    if (page == null || projectId == null) return;
    try {
      await ref
          .read(apiClientProvider)
          .deletePage(projectId, page['id'].toString());
      _selectedPageId = null;
      await _loadDocument();
      _ctrl.reload();
    } catch (error) {
      if (mounted)
        NotificationService.error(context, 'Suppression impossible : $error');
    }
  }

  Future<void> _regeneratePage() async {
    final instruction = TextEditingController(
        text:
            'Améliore la structure et le contenu de cette page en respectant la marque.');
    final accepted = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
              title: const Text('Régénérer cette page avec l’IA'),
              content: SizedBox(
                  width: 480,
                  child: TextField(
                      controller: instruction,
                      maxLines: 5,
                      decoration:
                          const InputDecoration(labelText: 'Instructions'))),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(context, false),
                    child: const Text('Annuler')),
                FilledButton.icon(
                    onPressed: () => Navigator.pop(context, true),
                    icon: const Icon(Icons.auto_awesome),
                    label: const Text('Régénérer'))
              ],
            ));
    final page = _selectedPage;
    final projectId = ref.read(currentProjectIdProvider);
    if (accepted != true || page == null || projectId == null) return;
    setState(() => _busy = true);
    try {
      await ref
          .read(apiClientProvider)
          .regeneratePage(projectId, page['id'].toString(), instruction.text);
      await _loadDocument();
      _ctrl.reload();
      if (mounted)
        NotificationService.success(
            context, 'Page régénérée. Tu peux annuler cette action.');
    } catch (error) {
      if (mounted)
        NotificationService.error(context, 'Régénération impossible : $error');
    } finally {
      instruction.dispose();
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _addComponent() async {
    final type = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
          child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Ajouter un élément',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 14),
              Wrap(spacing: 10, runSpacing: 10, children: const [
                _ComponentChoice(
                    type: 'Section',
                    label: 'Section',
                    icon: Icons.view_agenda_outlined),
                _ComponentChoice(
                    type: 'Title', label: 'Titre', icon: Icons.title),
                _ComponentChoice(
                    type: 'Text', label: 'Texte', icon: Icons.notes),
                _ComponentChoice(
                    type: 'Image', label: 'Image', icon: Icons.image_outlined),
                _ComponentChoice(
                    type: 'Button',
                    label: 'Bouton',
                    icon: Icons.smart_button_outlined),
              ]),
            ]),
      )),
    );
    final projectId = ref.read(currentProjectIdProvider);
    final page = _selectedPage;
    if (type == null || projectId == null || page == null) return;
    setState(() => _busy = true);
    try {
      await ref
          .read(apiClientProvider)
          .createPageComponent(projectId, page['id'].toString(), type);
      await _loadDocument();
      _ctrl.reload();
      if (mounted)
        NotificationService.success(context, '$type ajouté à la page.');
    } catch (error) {
      if (mounted)
        NotificationService.error(context, 'Ajout impossible : $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _saveCode() async {
    final projectId = ref.read(currentProjectIdProvider);
    if (projectId == null) return;
    setState(() => _busy = true);
    try {
      final decoded = jsonDecode(_codeCtrl.text);
      if (decoded is! Map<String, dynamic>)
        throw const FormatException('Le document doit être un objet JSON.');
      await ref
          .read(apiClientProvider)
          .replaceProjectDocument(projectId, decoded);
      await _loadDocument();
      _ctrl.reload();
      if (mounted)
        NotificationService.success(context, 'Code validé et enregistré.');
    } catch (error) {
      if (mounted)
        NotificationService.error(context, 'Document invalide : $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _askCodeAi() async {
    final projectId = ref.read(currentProjectIdProvider);
    final prompt = _codeAiCtrl.text.trim();
    if (projectId == null || prompt.isEmpty) return;
    setState(() => _busy = true);
    try {
      final answer =
          await ref.read(apiClientProvider).chatWithProject(projectId, [
        {
          'role': 'user',
          'content':
              'Tu aides à modifier un document JSON de composants. $prompt'
        }
      ]);
      if (mounted)
        showDialog<void>(
            context: context,
            builder: (context) => AlertDialog(
                    title: const Text('Suggestion IA'),
                    content: SelectableText(answer),
                    actions: [
                      FilledButton(
                          onPressed: () => Navigator.pop(context),
                          child: const Text('Fermer'))
                    ]));
    } catch (error) {
      if (mounted)
        NotificationService.error(
            context, 'Assistant IA indisponible : $error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final nonce =
        ref.watch(projectWorkspaceProvider.select((s) => s.previewNonce));
    final api = ref.read(apiClientProvider);

    return PageScaffold(
      title: 'Studio de création',
      subtitle: _mode == _EditorMode.visual
          ? 'Mode visuel — simple et guidé'
          : 'Mode Code + IA — contrôle avancé',
      action: Wrap(crossAxisAlignment: WrapCrossAlignment.center, children: [
        SegmentedButton<_EditorMode>(segments: const [
          ButtonSegment(
              value: _EditorMode.visual,
              icon: Icon(Icons.dashboard_customize_outlined),
              label: Text('Visuel')),
          ButtonSegment(
              value: _EditorMode.code,
              icon: Icon(Icons.code),
              label: Text('Code + IA')),
        ], selected: {
          _mode
        }, onSelectionChanged: (value) => setState(() => _mode = value.first)),
        const SizedBox(width: 10),
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
        if (_loading)
          const Center(
              child: Padding(
                  padding: EdgeInsets.all(48),
                  child: CircularProgressIndicator()))
        else if (nonce == null)
          const Padding(
            padding: EdgeInsets.all(24),
            child: Text('Aucun aperçu disponible. Génère d’abord ton site.'),
          )
        else if (_mode == _EditorMode.code)
          _CodeWorkspace(
              controller: _codeCtrl,
              aiController: _codeAiCtrl,
              busy: _busy,
              onSave: _saveCode,
              onAskAi: _askCodeAi)
        else
          SizedBox(
            height: MediaQuery.of(context).size.height - 180,
            child: LayoutBuilder(
              builder: (ctx, c) {
                final wide = c.maxWidth > 900;
                final hasSelection = _selected != null;
                final preview = Center(
                    child: AnimatedContainer(
                  duration: const Duration(milliseconds: 220),
                  width: _viewport.width,
                  clipBehavior: Clip.antiAlias,
                  decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.borderSoft)),
                  child: EditorIframe(
                    key: ValueKey('${_selectedPageId}_${_viewport.name}'),
                    url: api.previewUrl(nonce, edit: true, page: _selectedSlug),
                    controller: _ctrl,
                    onSelect: _onSelect,
                  ),
                ));
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
                        right: 0,
                        top: 0,
                        bottom: 0,
                        width: c.maxWidth.clamp(280, 380).toDouble(),
                        child: Material(elevation: 4, child: panel),
                      ),
                  ]);
                }
                return Column(children: [
                  _EditorToolbar(
                      viewport: _viewport,
                      onViewport: (value) => setState(() => _viewport = value),
                      onAdd: _addComponent,
                      onRegenerate: _regeneratePage),
                  const SizedBox(height: 10),
                  Expanded(
                      child: Row(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                        SizedBox(
                            width: 230,
                            child: _PagesPanel(
                                pages: _pages,
                                selectedId: _selectedPageId,
                                onSelect: (id) => setState(() {
                                      _selectedPageId = id;
                                      _selected = null;
                                    }),
                                onAdd: _createPage,
                                onDelete: _deletePage)),
                        const SizedBox(width: 12),
                        Expanded(child: preview),
                        if (hasSelection) ...[
                          const SizedBox(width: 12),
                          SizedBox(width: 360, child: panel),
                        ],
                      ]))
                ]);
              },
            ),
          ),
      ],
    );
  }
}

enum _EditorMode { visual, code }

enum _Viewport {
  desktop(1180, 'Ordinateur', Icons.desktop_windows_outlined),
  tablet(768, 'Tablette', Icons.tablet_mac_outlined),
  mobile(390, 'Mobile', Icons.phone_iphone_outlined);

  const _Viewport(this.width, this.label, this.icon);
  final double width;
  final String label;
  final IconData icon;
}

class _EditorToolbar extends StatelessWidget {
  const _EditorToolbar(
      {required this.viewport,
      required this.onViewport,
      required this.onAdd,
      required this.onRegenerate});
  final _Viewport viewport;
  final ValueChanged<_Viewport> onViewport;
  final VoidCallback onAdd;
  final VoidCallback onRegenerate;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(children: [
              const Icon(Icons.visibility_outlined, size: 18),
              const SizedBox(width: 8),
              const Text('Aperçu responsive',
                  style: TextStyle(fontWeight: FontWeight.w700)),
              const Spacer(),
              SegmentedButton<_Viewport>(
                showSelectedIcon: false,
                segments: [
                  for (final item in _Viewport.values)
                    ButtonSegment(
                        value: item, icon: Icon(item.icon), tooltip: item.label)
                ],
                selected: {viewport},
                onSelectionChanged: (value) => onViewport(value.first),
              ),
              const SizedBox(width: 10),
              FilledButton.icon(
                  onPressed: onAdd,
                  icon: const Icon(Icons.add, size: 17),
                  label: const Text('Ajouter')),
              const SizedBox(width: 8),
              OutlinedButton.icon(
                  onPressed: onRegenerate,
                  icon: const Icon(Icons.auto_awesome, size: 17),
                  label: const Text('Régénérer la page')),
            ])),
      );
}

class _ComponentChoice extends StatelessWidget {
  const _ComponentChoice(
      {required this.type, required this.label, required this.icon});
  final String type;
  final String label;
  final IconData icon;

  @override
  Widget build(BuildContext context) => SizedBox(
        width: 130,
        height: 92,
        child: OutlinedButton(
          onPressed: () => Navigator.pop(context, type),
          child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [Icon(icon), const SizedBox(height: 8), Text(label)]),
        ),
      );
}

class _PagesPanel extends StatelessWidget {
  const _PagesPanel(
      {required this.pages,
      required this.selectedId,
      required this.onSelect,
      required this.onAdd,
      required this.onDelete});
  final List<Map<String, dynamic>> pages;
  final String? selectedId;
  final ValueChanged<String> onSelect;
  final VoidCallback onAdd;
  final VoidCallback onDelete;

  String _title(Map<String, dynamic> page) {
    for (final section in ((page['slots']?['body'] as List?) ?? const [])) {
      for (final item
          in ((section['slots']?['content'] as List?) ?? const [])) {
        if (item['type'] == 'Title')
          return item['props']?['text']?.toString() ?? 'Page';
      }
    }
    return page['props']?['slug']?.toString() ?? 'Page';
  }

  @override
  Widget build(BuildContext context) => Card(
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Padding(
            padding: const EdgeInsets.fromLTRB(14, 14, 8, 8),
            child: Row(children: [
              const Expanded(
                  child: Text('PAGES',
                      style: TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 12,
                          letterSpacing: 1))),
              IconButton(
                  tooltip: 'Ajouter une page',
                  onPressed: onAdd,
                  icon: const Icon(Icons.add))
            ])),
        const Divider(height: 1),
        Expanded(
            child: ListView(padding: const EdgeInsets.all(8), children: [
          for (final page in pages)
            Padding(
                padding: const EdgeInsets.only(bottom: 5),
                child: ListTile(
                  selected: page['id'] == selectedId,
                  selectedTileColor: AppColors.primary.withValues(alpha: .14),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                  leading: const Icon(Icons.description_outlined, size: 19),
                  title: Text(_title(page),
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  subtitle:
                      Text('/${page['props']?['slug'] ?? ''}', maxLines: 1),
                  onTap: () => onSelect(page['id'].toString()),
                )),
        ])),
        Padding(
            padding: const EdgeInsets.all(10),
            child: OutlinedButton.icon(
                onPressed: pages.length > 1 ? onDelete : null,
                icon: const Icon(Icons.delete_outline, size: 17),
                label: const Text('Supprimer'))),
      ]));
}

class _CodeWorkspace extends StatelessWidget {
  const _CodeWorkspace(
      {required this.controller,
      required this.aiController,
      required this.busy,
      required this.onSave,
      required this.onAskAi});
  final TextEditingController controller;
  final TextEditingController aiController;
  final bool busy;
  final VoidCallback onSave;
  final VoidCallback onAskAi;

  @override
  Widget build(BuildContext context) => SizedBox(
        height: MediaQuery.sizeOf(context).height - 190,
        child: Row(children: [
          Expanded(
              flex: 7,
              child: Card(
                  child: Column(children: [
                Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(children: [
                      const Icon(Icons.data_object, color: AppColors.primary),
                      const SizedBox(width: 8),
                      const Expanded(
                          child: Text('Document de composants JSON',
                              style: TextStyle(fontWeight: FontWeight.w800))),
                      FilledButton.icon(
                          onPressed: busy ? null : onSave,
                          icon: const Icon(Icons.save_outlined, size: 17),
                          label: const Text('Valider et enregistrer')),
                    ])),
                const Divider(height: 1),
                Expanded(
                    child: TextField(
                  controller: controller,
                  expands: true,
                  maxLines: null,
                  minLines: null,
                  keyboardType: TextInputType.multiline,
                  style: const TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 13,
                      height: 1.45,
                      color: Color(0xFFD1E7FF)),
                  decoration: const InputDecoration(
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.all(18),
                      filled: true,
                      fillColor: Color(0xFF080D16)),
                )),
              ]))),
          const SizedBox(width: 12),
          SizedBox(
              width: 340,
              child: Card(
                  child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            const Row(children: [
                              Icon(Icons.auto_awesome, color: AppColors.cyan),
                              SizedBox(width: 8),
                              Text('Copilote IA',
                                  style: TextStyle(fontWeight: FontWeight.w800))
                            ]),
                            const SizedBox(height: 8),
                            const Text(
                                'Demande une structure, une correction ou un composant. L’IA connaît le contexte du projet.',
                                style: TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 12)),
                            const SizedBox(height: 16),
                            Expanded(
                                child: TextField(
                                    controller: aiController,
                                    maxLines: null,
                                    expands: true,
                                    decoration: const InputDecoration(
                                        hintText:
                                            'Ex. Ajoute une page Tarifs avec trois offres…',
                                        alignLabelWithHint: true))),
                            const SizedBox(height: 12),
                            FilledButton.icon(
                                onPressed: busy ? null : onAskAi,
                                icon: busy
                                    ? const SizedBox(
                                        width: 16,
                                        height: 16,
                                        child: CircularProgressIndicator(
                                            strokeWidth: 2))
                                    : const Icon(Icons.send_outlined),
                                label: const Text('Demander à l’IA')),
                            const SizedBox(height: 10),
                            const Text(
                                'Le JSON est validé par le SDK avant enregistrement. Une version précédente reste disponible via Annuler.',
                                style: TextStyle(
                                    color: AppColors.textMuted, fontSize: 11)),
                          ])))),
        ]),
      );
}

class _ChatBar extends StatefulWidget {
  const _ChatBar(
      {required this.enabled, required this.hint, required this.onSend});
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
        border:
            Border(top: BorderSide(color: theme.dividerColor.withOpacity(0.6))),
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
                  ? [
                      BoxShadow(
                          color: theme.colorScheme.primary.withOpacity(0.08),
                          blurRadius: 14,
                          offset: const Offset(0, 4))
                    ]
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
                  color: canSend
                      ? theme.colorScheme.primary
                      : theme.colorScheme.outlineVariant,
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
                        color: canSend
                            ? theme.colorScheme.onPrimary
                            : theme.colorScheme.onSurfaceVariant,
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
                  style: theme.textTheme.labelSmall
                      ?.copyWith(color: theme.hintColor),
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

    final isText = const {
      'h1',
      'h2',
      'h3',
      'h4',
      'h5',
      'h6',
      'p',
      'span',
      'a',
      'button',
      'li',
      'label',
      'blockquote'
    }.contains(tag);
    final isImg = tag == 'img';
    final isInput = tag == 'input' || tag == 'textarea';
    final isContainer = const {
      'section',
      'div',
      'header',
      'footer',
      'main',
      'article',
      'aside',
      'nav',
      'form'
    }.contains(tag);
    final showTextField = isText || isContainer;

    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          // Header with tag + close
          Container(
            padding: const EdgeInsets.fromLTRB(12, 8, 4, 8),
            decoration: BoxDecoration(
                border: Border(
                    bottom: BorderSide(color: Theme.of(context).dividerColor))),
            child: Row(children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                    color: const Color(0xFFE0F2FE),
                    borderRadius: BorderRadius.circular(6)),
                child: Text('<$tag>',
                    style: const TextStyle(
                        color: Color(0xFF0EA5E9), fontWeight: FontWeight.w700)),
              ),
              const SizedBox(width: 8),
              Expanded(
                  child: Text(id,
                      style: Theme.of(context).textTheme.bodySmall,
                      overflow: TextOverflow.ellipsis)),
              if (busy)
                const Padding(
                    padding: EdgeInsets.only(right: 8),
                    child: SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2))),
              IconButton(
                  tooltip: 'Fermer',
                  onPressed: onClose,
                  icon: const Icon(Icons.close)),
            ]),
          ),
          // Properties (scrollable)
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (showTextField) ...[
                  Text(isContainer ? 'Texte (remplace le contenu)' : 'Texte',
                      style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  _TextEditor(
                    initial: text,
                    onSave: (v) => onApplyOps([
                      {'op': 'set_text', 'value': v}
                    ]),
                  ),
                  const SizedBox(height: 16),
                ],
                if (isImg) ...[
                  Text('Image', style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  _AttrEditor(
                      label: 'URL image',
                      initial: src,
                      onSave: (v) => onApplyOps([
                            {'op': 'set_attr', 'name': 'src', 'value': v}
                          ])),
                  const SizedBox(height: 8),
                  _AttrEditor(
                      label: 'Texte alt',
                      initial: (selected!['alt'] ?? '').toString(),
                      onSave: (v) => onApplyOps([
                            {'op': 'set_attr', 'name': 'alt', 'value': v}
                          ])),
                  const SizedBox(height: 16),
                ],
                if (tag == 'a') ...[
                  _AttrEditor(
                      label: 'Lien (href)',
                      initial: href,
                      onSave: (v) => onApplyOps([
                            {'op': 'set_attr', 'name': 'href', 'value': v}
                          ])),
                  const SizedBox(height: 16),
                ],
                if (isInput) ...[
                  Text('Champ', style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 8),
                  _AttrEditor(
                      label: 'Placeholder',
                      initial: '',
                      onSave: (v) => onApplyOps([
                            {
                              'op': 'set_attr',
                              'name': 'placeholder',
                              'value': v
                            }
                          ])),
                  const SizedBox(height: 8),
                  _AttrEditor(
                      label: 'Type',
                      initial: '',
                      onSave: (v) => onApplyOps([
                            {'op': 'set_attr', 'name': 'type', 'value': v}
                          ])),
                  const SizedBox(height: 16),
                ],
                Text('Apparence',
                    style: Theme.of(context).textTheme.titleSmall),
                const SizedBox(height: 8),
                _ColorRow(
                    label: 'Fond',
                    onPick: (token) => onApplyOps([
                          {
                            'op': 'set_style_token',
                            'name': 'background-color',
                            'token': token
                          }
                        ])),
                const SizedBox(height: 8),
                _ColorRow(
                    label: 'Texte',
                    onPick: (token) => onApplyOps([
                          {
                            'op': 'set_style_token',
                            'name': 'color',
                            'token': token
                          }
                        ])),
                if (isContainer) ...[
                  const SizedBox(height: 12),
                  Wrap(spacing: 8, runSpacing: 8, children: [
                    OutlinedButton(
                        onPressed: () => onApplyOps([
                              {
                                'op': 'set_style_token',
                                'name': 'padding',
                                'token': 'theme.spacing.md'
                              }
                            ]),
                        child: const Text('Padding 24')),
                    OutlinedButton(
                        onPressed: () => onApplyOps([
                              {
                                'op': 'set_style_token',
                                'name': 'padding',
                                'token': 'theme.spacing.lg'
                              }
                            ]),
                        child: const Text('Padding 48')),
                    OutlinedButton(
                        onPressed: () => onApplyOps([
                              {
                                'op': 'set_style_token',
                                'name': 'border-radius',
                                'token': 'theme.radius.medium'
                              }
                            ]),
                        child: const Text('Radius 16')),
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
  late final TextEditingController _ctrl =
      TextEditingController(text: widget.initial);
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
        decoration: const InputDecoration(
            labelText: 'Texte', border: OutlineInputBorder()),
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
  const _AttrEditor(
      {required this.label, required this.initial, required this.onSave});
  final String label;
  final String initial;
  final void Function(String) onSave;

  @override
  State<_AttrEditor> createState() => _AttrEditorState();
}

class _AttrEditorState extends State<_AttrEditor> {
  late final TextEditingController _ctrl =
      TextEditingController(text: widget.initial);

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
          decoration: InputDecoration(
              labelText: widget.label,
              border: const OutlineInputBorder(),
              isDense: true),
          onSubmitted: widget.onSave,
        ),
      ),
      const SizedBox(width: 8),
      IconButton(
          onPressed: () => widget.onSave(_ctrl.text),
          icon: const Icon(Icons.check)),
    ]);
  }
}

class _ColorRow extends StatelessWidget {
  const _ColorRow({required this.label, required this.onPick});
  final String label;
  final void Function(String) onPick;

  static const _colors = <String, Color>{
    'theme.colors.primary': Color(0xFF6366F1),
    'theme.colors.secondary': Color(0xFF22D3EE),
    'theme.colors.accent': Color(0xFFF97316),
    'theme.colors.bg': Color(0xFF0F1117),
    'theme.colors.surface': Color(0xFF161B27),
    'theme.colors.text': Color(0xFFF8FAFC),
    'theme.colors.muted': Color(0xFF94A3B8),
  };

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      SizedBox(width: 60, child: Text(label)),
      Expanded(
        child: Wrap(
          spacing: 6,
          runSpacing: 6,
          children: _colors.entries.map((entry) {
            return InkWell(
              onTap: () => onPick(entry.key),
              child: Tooltip(
                message: entry.key,
                child: Container(
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    color: entry.value,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.black26),
                  ),
                  child: null,
                ),
              ),
            );
          }).toList(),
        ),
      ),
    ]);
  }
}
