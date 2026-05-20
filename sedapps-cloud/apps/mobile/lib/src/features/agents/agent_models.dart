class AgentRunView {
  const AgentRunView({
    required this.name,
    required this.status,
    required this.model,
    required this.durationMs,
    required this.tokensIn,
    required this.tokensOut,
    required this.input,
    required this.output,
    required this.warnings,
  });

  factory AgentRunView.fromJson(Map<String, dynamic> json) {
    return AgentRunView(
      name: json['name']?.toString() ?? 'agent',
      status: json['status']?.toString() ?? 'unknown',
      model: json['model']?.toString() ?? 'model',
      durationMs: (json['duration_ms'] as num?)?.toInt() ?? 0,
      tokensIn: (json['tokens_in'] as num?)?.toInt() ?? 0,
      tokensOut: (json['tokens_out'] as num?)?.toInt() ?? 0,
      input: Map<String, dynamic>.from(json['input'] as Map? ?? {}),
      output: Map<String, dynamic>.from(json['output'] as Map? ?? {}),
      warnings: (json['warnings'] as List? ?? []).map((e) => e.toString()).toList(),
    );
  }

  final String name;
  final String status;
  final String model;
  final int durationMs;
  final int tokensIn;
  final int tokensOut;
  final Map<String, dynamic> input;
  final Map<String, dynamic> output;
  final List<String> warnings;
}

class AiJobView {
  const AiJobView({
    required this.id,
    required this.status,
    required this.workflow,
    required this.agents,
    required this.input,
    required this.output,
    this.error,
  });

  factory AiJobView.fromJson(Map<String, dynamic> json) {
    return AiJobView(
      id: json['id']?.toString() ?? '',
      status: json['status']?.toString() ?? 'queued',
      workflow: json['workflow']?.toString() ?? 'site_generation',
      error: json['error']?.toString(),
      input: Map<String, dynamic>.from(json['input'] as Map? ?? {}),
      output: Map<String, dynamic>.from(json['output'] as Map? ?? {}),
      agents: (json['agents'] as List? ?? [])
          .map((item) => AgentRunView.fromJson(Map<String, dynamic>.from(item as Map)))
          .toList(),
    );
  }

  final String id;
  final String status;
  final String workflow;
  final String? error;
  final Map<String, dynamic> input;
  final Map<String, dynamic> output;
  final List<AgentRunView> agents;
}
