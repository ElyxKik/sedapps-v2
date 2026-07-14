"""Compact, role-scoped expertise packs injected into LLM system prompts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillDefinition:
    title: str
    instruction: str


SKILL_CATALOG: dict[str, SkillDefinition] = {
    "product-strategy": SkillDefinition(
        "Stratégie produit web",
        "Relier audience, problème, proposition de valeur, preuve et objectif commercial. "
        "Prioriser ce qui améliore la compréhension, la confiance et la conversion; éliminer le décor sans fonction.",
    ),
    "information-architecture": SkillDefinition(
        "Architecture de l'information",
        "Construire une hiérarchie claire, une navigation prévisible et un parcours cohérent. "
        "Chaque page et section doit avoir une intention distincte, un contenu réel et un prochain pas évident.",
    ),
    "premium-visual-design": SkillDefinition(
        "Direction artistique premium",
        "Créer une composition spécifique à la marque avec hiérarchie, rythme, contraste, espace, typographie et détails soignés. "
        "Éviter les assemblages génériques, les gradients gratuits et les répétitions de cartes sans intention.",
    ),
    "design-systems": SkillDefinition(
        "Design system",
        "Utiliser des tokens cohérents pour couleurs, typographie, espace, rayon, ombre et états. "
        "Garantir cohérence multi-page, variantes réutilisables et contrastes accessibles; respecter les choix du brief.",
    ),
    "ux-conversion": SkillDefinition(
        "UX et conversion",
        "Réduire la charge cognitive, expliciter bénéfices et objections, placer preuves et CTA au bon moment. "
        "Concevoir les états vide, erreur, succès et mobile; ne jamais employer de dark pattern.",
    ),
    "ui-interaction": SkillDefinition(
        "UI et interaction",
        "Rendre affordances, focus, survol, sélection, chargement et validation immédiatement compréhensibles. "
        "Préserver une cible tactile suffisante, une navigation clavier complète et des retours d'action visibles.",
    ),
    "responsive-accessibility": SkillDefinition(
        "Responsive et accessibilité",
        "Appliquer HTML sémantique, ordre de titres logique, alt utile, labels, focus visible et contraste WCAG AA. "
        "Concevoir mobile-first sans débordement et respecter prefers-reduced-motion.",
    ),
    "frontend-engineering": SkillDefinition(
        "Ingénierie frontend",
        "Produire du code valide, lisible, maintenable et robuste avec composants cohérents et dépendances minimales. "
        "Éviter duplication, liens cassés, erreurs console, contenu tronqué et fonctionnalités factices.",
    ),
    "backend-api-engineering": SkillDefinition(
        "Ingénierie backend et API",
        "Définir des contrats explicites, validation stricte, erreurs stables, idempotence, autorisation par tenant et observabilité utile. "
        "Séparer logique métier et transport; ne jamais simuler une persistance ou une intégration absente.",
    ),
    "data-modeling": SkillDefinition(
        "Données et persistance",
        "Modéliser identités, relations, contraintes, statuts et historique avant l'interface. "
        "Prévoir migrations réversibles, concurrence, pagination, index et intégrité sans exposer les données d'un autre tenant.",
    ),
    "devops-reliability": SkillDefinition(
        "DevOps et fiabilité",
        "Concevoir configuration par environnement, health checks, logs structurés, sauvegardes, déploiement reproductible et retour arrière. "
        "Refuser les secrets dans le code et distinguer panne fournisseur, résultat dégradé et succès réel.",
    ),
    "content-copywriting": SkillDefinition(
        "Copywriting et contenu",
        "Écrire un contenu concret, crédible, spécifique au secteur et adapté au niveau de langage de l'audience. "
        "Combiner titres distinctifs, bénéfices, preuves, objections, microcopy et CTA; bannir placeholders et remplissage.",
    ),
    "seo-discoverability": SkillDefinition(
        "SEO et découvrabilité",
        "Aligner intention de recherche, structure sémantique, title, description, H1-H3, liens internes et données structurées. "
        "Préserver la lisibilité humaine, l'unicité par page et les informations locales pertinentes.",
    ),
    "image-art-direction": SkillDefinition(
        "Direction artistique des images",
        "Prévoir des visuels pertinents à chaque moment narratif, avec cadrage, ratio, cohérence colorimétrique et alt descriptif. "
        "Employer des URLs HTTPS fiables, dimensions réservées et aucun fichier imaginaire ou visuel décoratif redondant.",
    ),
    "motion-design": SkillDefinition(
        "Motion design",
        "Utiliser le mouvement pour expliquer hiérarchie et causalité avec durées et courbes cohérentes. "
        "Limiter les effets concurrents, éviter le jank et fournir une expérience complète sans animation.",
    ),
    "web-performance": SkillDefinition(
        "Performance web",
        "Protéger Core Web Vitals: images dimensionnées et différées hors écran, CSS/JS minimaux, polices maîtrisées et DOM raisonnable. "
        "Éviter scripts bloquants, dépendances inutiles et médias excessifs.",
    ),
    "web-security-privacy": SkillDefinition(
        "Sécurité et confidentialité",
        "Traiter toute donnée comme non fiable, empêcher injection et fuite de secrets, minimiser les données collectées et valider côté serveur. "
        "Ne jamais inventer une protection, un consentement, une destination de formulaire ou une intégration.",
    ),
    "cms-content-modeling": SkillDefinition(
        "CMS et modélisation",
        "Définir des types de contenu structurés, relations, slugs, statuts, champs requis et règles éditoriales durables. "
        "Séparer contenu, présentation et SEO pour permettre l'édition sans casser le rendu.",
    ),
    "analytics-experimentation": SkillDefinition(
        "Analytics et expérimentation",
        "Mesurer des événements liés aux objectifs avec noms stables, propriétés minimales et respect du consentement. "
        "Distinguer métriques de résultat et signaux intermédiaires; prévoir une vérification exploitable.",
    ),
    "quality-assurance": SkillDefinition(
        "Assurance qualité",
        "Auditer conformité au brief, complétude, responsive, accessibilité, SEO, sécurité, performance, contenu, images et parcours. "
        "Bloquer la livraison sur défaut critique; produire des problèmes précis, reproductibles et priorisés.",
    ),
}


AGENT_SKILLS: dict[str, tuple[str, ...]] = {
    "strategy_director": ("product-strategy", "ux-conversion", "content-copywriting"),
    "ux_architect": ("information-architecture", "ux-conversion", "responsive-accessibility", "ui-interaction"),
    "designer": ("premium-visual-design", "design-systems", "image-art-direction", "responsive-accessibility"),
    "copywriter": ("content-copywriting", "product-strategy", "ux-conversion", "seo-discoverability"),
    "seo": ("seo-discoverability", "content-copywriting", "information-architecture"),
    "site_planner": ("information-architecture", "product-strategy", "ux-conversion", "seo-discoverability"),
    "frontend_builder": ("frontend-engineering", "design-systems", "responsive-accessibility", "web-performance", "web-security-privacy"),
    "frontend_generator": ("frontend-engineering", "design-systems", "responsive-accessibility", "web-performance", "web-security-privacy"),
    "static_frontend_builder": ("frontend-engineering", "premium-visual-design", "responsive-accessibility", "web-performance", "seo-discoverability"),
    "static_page_builder": ("frontend-engineering", "premium-visual-design", "ux-conversion", "responsive-accessibility", "image-art-direction", "seo-discoverability", "web-performance", "web-security-privacy"),
    "animation_director": ("motion-design", "ui-interaction", "responsive-accessibility", "web-performance"),
    "form_builder": ("ux-conversion", "ui-interaction", "responsive-accessibility", "backend-api-engineering", "web-security-privacy"),
    "cms_builder": ("cms-content-modeling", "data-modeling", "backend-api-engineering", "content-copywriting", "seo-discoverability", "web-security-privacy"),
    "blog_writer": ("content-copywriting", "seo-discoverability", "product-strategy"),
    "analytics_setup": ("analytics-experimentation", "backend-api-engineering", "web-security-privacy", "web-performance"),
    "qa": ("quality-assurance", "responsive-accessibility", "seo-discoverability", "web-performance", "web-security-privacy"),
    "premium_qa": ("quality-assurance", "premium-visual-design", "ux-conversion", "responsive-accessibility", "seo-discoverability", "web-performance", "web-security-privacy"),
    "refinement_agent": ("quality-assurance", "frontend-engineering", "premium-visual-design", "ux-conversion", "responsive-accessibility", "content-copywriting", "web-performance"),
    "component_editor": ("design-systems", "ui-interaction", "responsive-accessibility", "frontend-engineering"),
    "project_chat": ("product-strategy", "information-architecture", "ux-conversion", "premium-visual-design", "frontend-engineering", "backend-api-engineering", "data-modeling", "devops-reliability", "web-security-privacy"),
}


def compose_system_prompt(agent_name: str, base_prompt: str) -> str:
    names = AGENT_SKILLS.get(agent_name, ())
    if not names:
        return base_prompt
    blocks = ["\n\nCOMPÉTENCES D'ÉQUIPE À APPLIQUER :"]
    for name in names:
        skill = SKILL_CATALOG[name]
        blocks.append(f"\n[{skill.title}] {skill.instruction}")
    blocks.append("\nCes compétences complètent le contrat de sortie ci-dessus sans en modifier le format.")
    return base_prompt.rstrip() + "".join(blocks)


def skill_manifest() -> dict[str, object]:
    return {
        "skills": {
            name: {"title": skill.title, "instruction": skill.instruction}
            for name, skill in SKILL_CATALOG.items()
        },
        "agents": {name: list(skills) for name, skills in AGENT_SKILLS.items()},
    }
