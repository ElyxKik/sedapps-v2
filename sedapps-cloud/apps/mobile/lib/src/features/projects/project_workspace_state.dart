import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/api_client.dart';

final currentProjectIdProvider = StateProvider<String?>((ref) => null);

class SiteSection {
  const SiteSection({required this.id, required this.title, required this.content, this.enabled = true});

  final String id;
  final String title;
  final String content;
  final bool enabled;

  SiteSection copyWith({String? title, String? content, bool? enabled}) {
    return SiteSection(
      id: id,
      title: title ?? this.title,
      content: content ?? this.content,
      enabled: enabled ?? this.enabled,
    );
  }
}

class CmsArticle {
  const CmsArticle({required this.id, required this.title, required this.markdown, required this.status});

  final String id;
  final String title;
  final String markdown;
  final String status;

  CmsArticle copyWith({String? title, String? markdown, String? status}) {
    return CmsArticle(
      id: id,
      title: title ?? this.title,
      markdown: markdown ?? this.markdown,
      status: status ?? this.status,
    );
  }
}

class ChatMessage {
  const ChatMessage({
    required this.role,
    required this.text,
    this.tools = const [],
    this.agents = const [],
    this.isError = false,
    this.isPending = false,
  });

  final String role;
  final String text;
  final List<String> tools;
  final List<String> agents;
  final bool isError;
  final bool isPending;

  ChatMessage copyWith({String? text, bool? isPending, bool? isError, List<String>? tools, List<String>? agents}) {
    return ChatMessage(
      role: role,
      text: text ?? this.text,
      tools: tools ?? this.tools,
      agents: agents ?? this.agents,
      isError: isError ?? this.isError,
      isPending: isPending ?? this.isPending,
    );
  }
}

class PublishState {
  const PublishState({
    required this.subdomainEnabled,
    required this.customDomainEnabled,
    required this.domain,
    required this.status,
    this.url,
  });

  final bool subdomainEnabled;
  final bool customDomainEnabled;
  final String domain;
  final String status;
  final String? url;

  PublishState copyWith({
    bool? subdomainEnabled,
    bool? customDomainEnabled,
    String? domain,
    String? status,
    String? url,
  }) {
    return PublishState(
      subdomainEnabled: subdomainEnabled ?? this.subdomainEnabled,
      customDomainEnabled: customDomainEnabled ?? this.customDomainEnabled,
      domain: domain ?? this.domain,
      status: status ?? this.status,
      url: url ?? this.url,
    );
  }
}

class ProjectWorkspaceState {
  const ProjectWorkspaceState({
    required this.sections,
    required this.primaryColor,
    required this.headingFont,
    required this.articles,
    required this.selectedArticleId,
    required this.publish,
    required this.messages,
    required this.hasUnsavedChanges,
    this.previewNonce,
  });

  final List<SiteSection> sections;
  final String primaryColor;
  final String headingFont;
  final List<CmsArticle> articles;
  final String? selectedArticleId;
  final PublishState publish;
  final List<ChatMessage> messages;
  final bool hasUnsavedChanges;
  final String? previewNonce;

  CmsArticle? get selectedArticle {
    if (selectedArticleId == null) return articles.isEmpty ? null : articles.first;
    for (final article in articles) {
      if (article.id == selectedArticleId) return article;
    }
    return articles.isEmpty ? null : articles.first;
  }

  ProjectWorkspaceState copyWith({
    List<SiteSection>? sections,
    String? primaryColor,
    String? headingFont,
    List<CmsArticle>? articles,
    String? selectedArticleId,
    PublishState? publish,
    List<ChatMessage>? messages,
    bool? hasUnsavedChanges,
    String? previewNonce,
  }) {
    return ProjectWorkspaceState(
      sections: sections ?? this.sections,
      primaryColor: primaryColor ?? this.primaryColor,
      headingFont: headingFont ?? this.headingFont,
      articles: articles ?? this.articles,
      selectedArticleId: selectedArticleId ?? this.selectedArticleId,
      publish: publish ?? this.publish,
      messages: messages ?? this.messages,
      hasUnsavedChanges: hasUnsavedChanges ?? this.hasUnsavedChanges,
      previewNonce: previewNonce ?? this.previewNonce,
    );
  }
}

class ProjectWorkspaceNotifier extends StateNotifier<ProjectWorkspaceState> {
  ProjectWorkspaceNotifier(this._ref)
      : super(
          const ProjectWorkspaceState(
            sections: [
              SiteSection(id: 'hero', title: 'Hero', content: 'Créez votre présence web avec une équipe experte.'),
              SiteSection(id: 'features', title: 'Services', content: 'Design, développement, SEO et maintenance.'),
              SiteSection(id: 'faq', title: 'FAQ', content: 'Réponses aux questions fréquentes de vos clients.'),
              SiteSection(id: 'contact', title: 'Contact', content: 'Formulaire de contact et coordonnées.'),
            ],
            primaryColor: '#0EA5E9',
            headingFont: 'Inter',
            articles: [
              CmsArticle(id: 'art-1', title: 'Les tendances du web design 2025', markdown: '# Tendances 2025\n\nDesign moderne, rapide et responsive.', status: 'published'),
              CmsArticle(id: 'art-2', title: 'Guide complet du responsive design', markdown: '# Responsive design\n\nOptimise ton site pour tous les écrans.', status: 'draft'),
            ],
            selectedArticleId: 'art-1',
            publish: PublishState(subdomainEnabled: true, customDomainEnabled: false, domain: 'monsite.sedapps.cloud', status: 'draft'),
            messages: [
              ChatMessage(
                role: 'assistant',
                text: 'Bienvenue ! Je suis le Générateur IA SedApps. Demande-moi de modifier ton site, créer un article CMS, ajuster les couleurs, préparer un déploiement…',
                tools: ['workspace', 'cms', 'design', 'publish'],
              ),
            ],
            hasUnsavedChanges: false,
          ),
        );

  final Ref _ref;

  void updateSection(String id, {String? title, String? content, bool? enabled}) {
    state = state.copyWith(
      sections: state.sections.map((section) {
        if (section.id != id) return section;
        return section.copyWith(title: title, content: content, enabled: enabled);
      }).toList(),
      hasUnsavedChanges: true,
    );
  }

  void moveSection(int oldIndex, int newIndex) {
    final sections = [...state.sections];
    if (newIndex > oldIndex) newIndex -= 1;
    final item = sections.removeAt(oldIndex);
    sections.insert(newIndex, item);
    state = state.copyWith(sections: sections, hasUnsavedChanges: true);
  }

  void updateDesign({String? primaryColor, String? headingFont}) {
    state = state.copyWith(
      primaryColor: primaryColor,
      headingFont: headingFont,
      hasUnsavedChanges: true,
    );
  }

  void saveEditor() {
    state = state.copyWith(hasUnsavedChanges: false);
  }

  void selectArticle(String id) {
    state = state.copyWith(selectedArticleId: id);
  }

  void createArticle() {
    final id = 'art-${DateTime.now().millisecondsSinceEpoch}';
    final article = CmsArticle(id: id, title: 'Nouvel article', markdown: '# Nouvel article\n\nCommence à écrire ici.', status: 'draft');
    state = state.copyWith(articles: [article, ...state.articles], selectedArticleId: id, hasUnsavedChanges: true);
  }

  void updateSelectedArticle({String? title, String? markdown, String? status}) {
    final selected = state.selectedArticle;
    if (selected == null) return;
    state = state.copyWith(
      articles: state.articles.map((article) {
        if (article.id != selected.id) return article;
        return article.copyWith(title: title, markdown: markdown, status: status);
      }).toList(),
      hasUnsavedChanges: true,
    );
  }

  void deleteArticle(String id) {
    final articles = state.articles.where((article) => article.id != id).toList();
    state = state.copyWith(
      articles: articles,
      selectedArticleId: articles.isEmpty ? null : articles.first.id,
      hasUnsavedChanges: true,
    );
  }

  void updatePublish({bool? subdomainEnabled, bool? customDomainEnabled, String? domain}) {
    state = state.copyWith(
      publish: state.publish.copyWith(
        subdomainEnabled: subdomainEnabled,
        customDomainEnabled: customDomainEnabled,
        domain: domain,
      ),
    );
  }

  void syncFromProject(Map<String, dynamic> project) {
    final rawSections = project['sections'];
    final sections = <SiteSection>[];
    if (rawSections is List) {
      for (final item in rawSections) {
        if (item is Map) {
          final id = item['id']?.toString() ?? 'section-${sections.length}';
          final title = item['title']?.toString() ?? '';
          final content = item['content']?.toString() ?? '';
          final enabled = item['enabled'] is bool ? item['enabled'] as bool : true;
          sections.add(SiteSection(id: id, title: title, content: content, enabled: enabled));
        }
      }
    }

    final tokens = project['design_tokens'];
    String primary = state.primaryColor;
    String heading = state.headingFont;
    if (tokens is Map) {
      final tokenPrimary = tokens['primary'];
      if (tokenPrimary is String && tokenPrimary.startsWith('#')) primary = tokenPrimary;
      final tokenFont = tokens['font_heading'];
      if (tokenFont is String && tokenFont.isNotEmpty) heading = tokenFont;
    }

    final domain = project['domain']?.toString() ?? state.publish.domain;
    final publishedUrl = project['published_url']?.toString();
    final status = project['status']?.toString() == 'published' ? 'published' : state.publish.status;
    final nonce = project['preview_nonce']?.toString();

    // Stocker le brief du projet pour le chat
    final brief = project['brief'] as Map<String, dynamic>? ?? {};
    _projectBrief = brief;

    state = state.copyWith(
      sections: sections.isEmpty ? state.sections : sections,
      primaryColor: primary,
      headingFont: heading,
      publish: state.publish.copyWith(domain: domain, url: publishedUrl, status: status),
      hasUnsavedChanges: false,
      previewNonce: nonce,
    );
  }

  Map<String, dynamic> _projectBrief = {};

  Future<void> publishSite() async {
    state = state.copyWith(publish: state.publish.copyWith(status: 'building'));
    await Future<void>.delayed(const Duration(milliseconds: 600));
    state = state.copyWith(publish: state.publish.copyWith(status: 'uploading'));
    await Future<void>.delayed(const Duration(milliseconds: 600));
    state = state.copyWith(publish: state.publish.copyWith(status: 'published', url: 'https://${state.publish.domain}'));
  }

  void addUserMessage(String text) {
    if (text.trim().isEmpty) return;
    state = state.copyWith(messages: [...state.messages, ChatMessage(role: 'user', text: text.trim())]);
  }

  Future<void> askAi(String text) async {
    if (text.trim().isEmpty) return;
    addUserMessage(text);

    // Quick local intent detection so we can show tool tags + apply side-effects.
    final lower = text.toLowerCase();
    final tools = <String>[];
    final agents = <String>[];
    if (lower.contains('couleur') || lower.contains('palette') || lower.contains('design') || lower.contains('police')) {
      tools.add('design.update');
      agents.add('Designer');
    }
    if (lower.contains('article') || lower.contains('blog') || lower.contains('cms')) {
      tools.add('cms.create_article');
      agents.add('Rédacteur');
    }
    if (lower.contains('seo') || lower.contains('meta') || lower.contains('mots clés')) {
      tools.add('seo.optimize');
      agents.add('SEO Specialist');
    }
    if (lower.contains('publie') || lower.contains('déploie') || lower.contains('deploy') || lower.contains('mise en ligne')) {
      tools.add('publish.deploy');
      agents.add('Publisher');
    }
    if (lower.contains('section') || lower.contains('hero') || lower.contains('texte') || lower.contains('réécris')) {
      tools.add('workspace.update_section');
      agents.add('Copywriter');
    }
    if (agents.isEmpty) {
      agents.add('Conversationnel');
      tools.add('chat.respond');
    }

    final pending = ChatMessage(role: 'assistant', text: '...', isPending: true, tools: tools, agents: agents);
    state = state.copyWith(messages: [...state.messages, pending]);

    // Apply local side-effects optimistically.
    if (tools.contains('design.update')) {
      if (lower.contains('rouge')) updateDesign(primaryColor: '#EF4444');
      else if (lower.contains('vert')) updateDesign(primaryColor: '#10B981');
      else if (lower.contains('violet')) updateDesign(primaryColor: '#7C3AED');
      else if (lower.contains('orange')) updateDesign(primaryColor: '#F59E0B');
      else if (lower.contains('bleu') || lower.contains('couleur')) updateDesign(primaryColor: '#2563EB');
    }
    if (tools.contains('cms.create_article') && lower.contains('crée')) {
      createArticle();
    }

    final projectId = _ref.read(currentProjectIdProvider);
    String responseText;
    bool isError = false;
    try {
      if (projectId == null || projectId.isEmpty) {
        throw StateError('Aucun projet actif.');
      }
      final history = state.messages
          .where((m) => !m.isPending)
          .map((m) => {'role': m.role, 'text': m.text})
          .toList();
      responseText = await _ref.read(apiClientProvider).chatWithProject(projectId, history);
      if (responseText.trim().isEmpty) {
        responseText = 'Réponse vide reçue de l’IA.';
        isError = true;
      }
    } catch (error) {
      responseText = 'Erreur de connexion au Générateur IA : $error';
      isError = true;
    }

    // Replace pending message with final.
    final updated = [...state.messages];
    final idx = updated.lastIndexWhere((m) => m.isPending);
    if (idx >= 0) {
      updated[idx] = pending.copyWith(text: responseText, isPending: false, isError: isError);
    } else {
      updated.add(ChatMessage(role: 'assistant', text: responseText, tools: tools, agents: agents, isError: isError));
    }
    state = state.copyWith(messages: updated);
  }
}

final projectWorkspaceProvider = StateNotifierProvider<ProjectWorkspaceNotifier, ProjectWorkspaceState>((ref) {
  return ProjectWorkspaceNotifier(ref);
});
