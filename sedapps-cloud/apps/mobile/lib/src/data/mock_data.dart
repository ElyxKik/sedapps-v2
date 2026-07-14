const bool useMockData = bool.fromEnvironment('MOCK_DATA', defaultValue: false);

final mockProjects = [
  {
    'id': 'proj-1',
    'name': 'Mon Agence Web',
    'status': 'published',
    'created_at': '2025-01-15T10:30:00Z',
  },
  {
    'id': 'proj-2',
    'name': 'E-commerce Mode',
    'status': 'draft',
    'created_at': '2025-02-20T14:45:00Z',
  },
  {
    'id': 'proj-3',
    'name': 'Blog Tech',
    'status': 'published',
    'created_at': '2025-03-10T09:15:00Z',
  },
];

final mockJob = {
  'id': 'job-123',
  'status': 'success',
  'workflow': 'site_generation',
  'error': null,
  'input': {
    'business_name': 'Mon Agence Web',
    'sector': 'Services numériques',
    'brief':
        'Agence spécialisée en création de sites web modernes et responsifs',
  },
  'output': {
    'site_schema': {'pages': 5, 'sections': 12},
    'design_tokens': {'primary': '#5B5CF6', 'secondary': '#FF6B6B'},
  },
  'started_at': '2025-03-15T10:00:00Z',
  'finished_at': '2025-03-15T10:45:00Z',
  'tokens_in': 2500,
  'tokens_out': 3200,
  'cost_cents': 45,
  'agents': [
    {
      'id': 'agent-1',
      'name': 'designer',
      'status': 'ok',
      'model': 'claude-3.5-sonnet',
      'prompt_version': 1,
      'duration_ms': 8500,
      'tokens_in': 450,
      'tokens_out': 680,
      'input': {'brief': 'Créer un design moderne pour une agence web'},
      'output': {
        'colors': ['#5B5CF6', '#FF6B6B', '#F0F0F0'],
        'fonts': ['Inter', 'Playfair Display'],
        'layout': 'modern_minimal',
      },
      'warnings': [],
      'created_at': '2025-03-15T10:00:00Z',
    },
    {
      'id': 'agent-2',
      'name': 'copywriter',
      'status': 'ok',
      'model': 'claude-3.5-sonnet',
      'prompt_version': 1,
      'duration_ms': 6200,
      'tokens_in': 380,
      'tokens_out': 920,
      'input': {
        'business_name': 'Mon Agence Web',
        'sector': 'Services numériques'
      },
      'output': {
        'hero_title': 'Créez votre présence web avec nous',
        'hero_subtitle': 'Des sites modernes, responsifs et performants',
        'cta': 'Commencer maintenant',
      },
      'warnings': [],
      'created_at': '2025-03-15T10:08:30Z',
    },
    {
      'id': 'agent-3',
      'name': 'seo_specialist',
      'status': 'ok',
      'model': 'claude-3.5-sonnet',
      'prompt_version': 1,
      'duration_ms': 5100,
      'tokens_in': 420,
      'tokens_out': 650,
      'input': {
        'business_name': 'Mon Agence Web',
        'keywords': ['agence web', 'création site', 'web design']
      },
      'output': {
        'meta_title': 'Agence Web Professionnelle | Création de Sites Modernes',
        'meta_description':
            'Créez votre site web avec notre agence spécialisée en design et développement web.',
        'keywords': ['agence web', 'création site', 'web design', 'responsive'],
      },
      'warnings': [],
      'created_at': '2025-03-15T10:14:00Z',
    },
    {
      'id': 'agent-4',
      'name': 'frontend_developer',
      'status': 'ok',
      'model': 'claude-3.5-sonnet',
      'prompt_version': 1,
      'duration_ms': 12300,
      'tokens_in': 580,
      'tokens_out': 1200,
      'input': {
        'design_tokens': {'primary': '#5B5CF6'},
        'sections': ['hero', 'features', 'cta']
      },
      'output': {
        'components': ['Button', 'Card', 'Hero', 'Navigation'],
        'framework': 'React',
        'responsive': true,
      },
      'warnings': ['Consider adding animations for better UX'],
      'created_at': '2025-03-15T10:20:00Z',
    },
  ],
};

final mockArticles = [
  {
    'id': 'art-1',
    'title': 'Les tendances du web design 2025',
    'slug': 'tendances-web-design-2025',
    'status': 'published',
    'created_at': '2025-03-10T10:00:00Z',
  },
  {
    'id': 'art-2',
    'title': 'Guide complet du responsive design',
    'slug': 'guide-responsive-design',
    'status': 'draft',
    'created_at': '2025-03-12T14:30:00Z',
  },
];
