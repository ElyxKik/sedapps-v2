import 'dart:convert';

import 'package:flutter/material.dart';

import 'agent_models.dart';

class AgentTimeline extends StatelessWidget {
  const AgentTimeline({required this.job, super.key});

  final AiJobView? job;

  @override
  Widget build(BuildContext context) {
    if (job == null) {
      return const _EmptyAgents();
    }
    final agents = job!.agents;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.hub_outlined),
                const SizedBox(width: 8),
                Expanded(
                    child: Text('Interaction des agents IA',
                        style: Theme.of(context).textTheme.titleLarge)),
                Chip(label: Text(job!.status)),
              ],
            ),
            const SizedBox(height: 12),
            if (agents.isEmpty)
              const Text('Aucun agent exécuté pour le moment.'),
            for (var i = 0; i < agents.length; i++)
              _AgentTile(index: i + 1, agent: agents[i]),
          ],
        ),
      ),
    );
  }
}

class _AgentTile extends StatelessWidget {
  const _AgentTile({required this.index, required this.agent});

  final int index;
  final AgentRunView agent;

  @override
  Widget build(BuildContext context) {
    final ok = agent.status == 'ok' || agent.status == 'success';
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor: ok ? Colors.green.shade50 : Colors.orange.shade50,
          child: Text('$index'),
        ),
        title: Text(agent.name.replaceAll('_', ' ')),
        subtitle: Text(
            '${agent.model} · ${agent.durationMs} ms · ${agent.tokensIn + agent.tokensOut} tokens'),
        trailing: Chip(label: Text(agent.status)),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        children: [
          if (agent.warnings.isNotEmpty)
            Align(
                alignment: Alignment.centerLeft,
                child: Text('Warnings: ${agent.warnings.join(', ')}')),
          const SizedBox(height: 8),
          _JsonBlock(title: 'Entrée agent', value: agent.input),
          const SizedBox(height: 8),
          _JsonBlock(title: 'Sortie agent', value: agent.output),
        ],
      ),
    );
  }
}

class _JsonBlock extends StatelessWidget {
  const _JsonBlock({required this.title, required this.value});

  final String title;
  final Map<String, dynamic> value;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
          color: Colors.black87, borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(
                  color: Colors.white70, fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          SelectableText(
            const JsonEncoder.withIndent('  ').convert(value),
            style: const TextStyle(
                color: Colors.white, fontFamily: 'monospace', fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class _EmptyAgents extends StatelessWidget {
  const _EmptyAgents();

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Interaction des agents IA',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            const Text(
                'Lance une génération pour voir chaque agent travailler : designer, copywriter, SEO, frontend, CMS, formulaire, analytics et QA.'),
          ],
        ),
      ),
    );
  }
}
