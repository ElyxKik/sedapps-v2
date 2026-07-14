from app.component_sdk import (
    apply_component_ops,
    build_component_ai_context,
    migrate_page_schema,
    render_component_document,
    validate_document,
)


def _legacy_schema():
    return {
        "pages": [{
            "slug": "home",
            "sections": [{
                "id": "hero-1",
                "type": "hero.split",
                "title": "Construisez plus vite",
                "description": "Une plateforme pilotée par composants.",
                "items": [{"title": "Rapide", "description": "Sans HTML libre."}],
            }],
        }]
    }


def test_migrates_legacy_sections_to_component_tree():
    tree = migrate_page_schema(_legacy_schema(), {"palette": {"primary": "#5B5EFF"}})
    document = validate_document(tree)
    assert document.type == "Website"
    assert document.design_system.colors["primary"] == "#5B5EFF"
    assert document.pages[0].slots["body"][0].type == "Section"


def test_ai_context_is_scoped_to_selected_component():
    tree = migrate_page_schema(_legacy_schema())
    context = build_component_ai_context(tree, "hero-1-title")
    assert context["scope"]["component_id"] == "hero-1-title"
    assert context["component"]["props"]["text"] == "Construisez plus vite"
    assert "Ne modifie aucun autre composant." in context["constraints"]


def test_rejects_unknown_properties():
    tree = migrate_page_schema(_legacy_schema())
    tree["pages"][0]["slots"]["body"][0]["props"]["raw_html"] = "<script />"
    try:
        validate_document(tree)
    except ValueError as exc:
        assert "unsupported props" in str(exc)
    else:
        raise AssertionError("invalid component was accepted")


def test_component_editor_updates_only_selected_instance():
    tree = migrate_page_schema(_legacy_schema())
    updated, element = apply_component_ops(
        tree,
        "hero-1-title",
        [{"op": "set_text", "value": "Nouveau titre"}],
    )
    assert element["props"]["text"] == "Nouveau titre"
    section = updated["pages"][0]["slots"]["body"][0]
    assert section["slots"]["content"][1]["props"]["text"].startswith("Une plateforme")


def test_component_editor_accepts_only_existing_design_tokens():
    tree = migrate_page_schema(_legacy_schema(), {"palette": {"primary": "#5B5EFF"}})
    updated, _ = apply_component_ops(
        tree,
        "hero-1-title",
        [{"op": "set_style_token", "path": "color", "token": "theme.colors.primary"}],
    )
    title = updated["pages"][0]["slots"]["body"][0]["slots"]["content"][0]
    assert title["styles"]["color"] == "theme.colors.primary"

    try:
        apply_component_ops(
            tree,
            "hero-1-title",
            [{"op": "set_style", "name": "color", "value": "#ff0000"}],
        )
    except ValueError as exc:
        assert "unsafe design token" in str(exc)
    else:
        raise AssertionError("raw style value was accepted")


def test_structured_renderer_escapes_content_and_marks_instances():
    tree = migrate_page_schema(_legacy_schema())
    tree["pages"][0]["slots"]["body"][0]["slots"]["content"][0]["props"]["text"] = "<script>alert(1)</script>"
    rendered = render_component_document(tree, "Test")
    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
    assert 'data-sed-id="hero-1-title"' in rendered
