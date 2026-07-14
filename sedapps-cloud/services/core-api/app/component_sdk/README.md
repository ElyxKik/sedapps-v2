# Component SDK

The Component SDK is the structured contract between generation, editor, preview and AI.
The canonical document is a versioned `Website` JSON tree. Each node is a component
instance with typed props, token-aware styles and named slots. Raw HTML is never an AI
editing surface.

The first release deliberately keeps the legacy generated files next to
`page_schema.component_tree`. This makes migration non-destructive while new editor and
renderer clients adopt the SDK. New AI editing must use the scoped context endpoint and
return structured operations against the selected component id.

Endpoints:

- `GET /v1/projects/components/sdk` returns component manifests for inspector generation.
- `GET /v1/projects/{project_id}/components/{component_id}/ai-context` returns the minimal,
  scoped AI context: manifest, props, styles, parent, children and design system.
