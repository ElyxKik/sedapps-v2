import 'package:flutter/material.dart';

import '../../../core/theme.dart';
import '../../../widgets/page_scaffold.dart';

class MediaTab extends StatelessWidget {
  const MediaTab({super.key});

  static const _media = [
    {'name': 'hero-banner.jpg', 'type': 'image', 'size': '420 KB'},
    {'name': 'logo.svg', 'type': 'image', 'size': '12 KB'},
    {'name': 'product-demo.mp4', 'type': 'video', 'size': '8.4 MB'},
    {'name': 'team-photo.jpg', 'type': 'image', 'size': '1.2 MB'},
    {'name': 'brochure.pdf', 'type': 'doc', 'size': '320 KB'},
    {'name': 'icon-cloud.png', 'type': 'image', 'size': '34 KB'},
    {'name': 'audio-podcast.mp3', 'type': 'audio', 'size': '4.2 MB'},
    {'name': 'screenshot.png', 'type': 'image', 'size': '180 KB'},
  ];

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SectionHeader(
              title: 'Bibliothèque média',
              subtitle: '47 fichiers · 124 MB utilisés sur 5 GB',
              trailing: FilledButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.upload, size: 18),
                label: const Text('Uploader'),
              ),
            ),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.skyBlueLight.withValues(alpha: 0.3),
                border: Border.all(
                    color: AppColors.skyBlue.withValues(alpha: 0.3),
                    style: BorderStyle.solid,
                    width: 2),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Column(
                children: [
                  const Icon(Icons.cloud_upload_outlined,
                      color: AppColors.skyBlue, size: 40),
                  const SizedBox(height: 8),
                  const Text('Glisse tes fichiers ici',
                      style:
                          TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                  const SizedBox(height: 4),
                  Text('ou clique pour parcourir · jusqu\'à 10 MB par fichier',
                      style: TextStyle(
                          color: AppColors.textSecondary, fontSize: 12)),
                ],
              ),
            ),
            const SizedBox(height: 20),
            LayoutBuilder(
              builder: (context, constraints) {
                final columns = constraints.maxWidth > 800
                    ? 6
                    : constraints.maxWidth > 500
                        ? 4
                        : 3;
                return GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: _media.length,
                  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: columns,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 0.95,
                  ),
                  itemBuilder: (context, index) =>
                      _MediaCard(media: _media[index]),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _MediaCard extends StatelessWidget {
  const _MediaCard({required this.media});
  final Map<String, dynamic> media;

  @override
  Widget build(BuildContext context) {
    final type = media['type'] as String;
    final iconData = {
      'image': Icons.image,
      'video': Icons.movie,
      'audio': Icons.audiotrack,
      'doc': Icons.description,
    }[type]!;
    final color = {
      'image': const Color(0xFF0EA5E9),
      'video': const Color(0xFF22D3EE),
      'audio': const Color(0xFFF59E0B),
      'doc': const Color(0xFF10B981),
    }[type]!;

    return Container(
      decoration: BoxDecoration(
          border: Border.all(color: AppColors.border),
          borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.08),
                borderRadius:
                    const BorderRadius.vertical(top: Radius.circular(11)),
              ),
              child: Center(child: Icon(iconData, color: color, size: 36)),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(media['name'] as String,
                    style: const TextStyle(
                        fontSize: 11, fontWeight: FontWeight.w600),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis),
                Text(media['size'] as String,
                    style: const TextStyle(
                        fontSize: 10, color: AppColors.textSecondary)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
