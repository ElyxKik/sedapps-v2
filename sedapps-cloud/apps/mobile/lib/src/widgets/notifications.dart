import 'package:flutter/material.dart';

import '../core/theme.dart';

enum NotificationType { success, error, warning, info }

class NotificationService {
  static void show(
    BuildContext context, {
    required String message,
    NotificationType type = NotificationType.info,
    Duration duration = const Duration(seconds: 3),
    SnackBarAction? action,
  }) {
    final colors = {
      NotificationType.success: const Color(0xFF10B981),
      NotificationType.error: AppColors.danger,
      NotificationType.warning: const Color(0xFFF59E0B),
      NotificationType.info: AppColors.skyBlue,
    };

    final icons = {
      NotificationType.success: Icons.check_circle,
      NotificationType.error: Icons.error,
      NotificationType.warning: Icons.warning_amber,
      NotificationType.info: Icons.info,
    };

    final color = colors[type]!;
    final icon = icons[type]!;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(icon, color: Colors.white, size: 20),
            const SizedBox(width: 12),
            Expanded(child: Text(message, style: const TextStyle(color: Colors.white))),
          ],
        ),
        backgroundColor: color,
        duration: duration,
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.all(16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        action: action,
      ),
    );
  }

  static void success(BuildContext context, String message, {Duration? duration}) {
    show(context, message: message, type: NotificationType.success, duration: duration ?? const Duration(seconds: 2));
  }

  static void error(BuildContext context, String message, {Duration? duration}) {
    show(context, message: message, type: NotificationType.error, duration: duration ?? const Duration(seconds: 4));
  }

  static void warning(BuildContext context, String message, {Duration? duration}) {
    show(context, message: message, type: NotificationType.warning, duration: duration ?? const Duration(seconds: 3));
  }

  static void info(BuildContext context, String message, {Duration? duration}) {
    show(context, message: message, type: NotificationType.info, duration: duration ?? const Duration(seconds: 3));
  }
}

class Toast extends StatefulWidget {
  const Toast({
    required this.message,
    this.type = NotificationType.info,
    this.duration = const Duration(seconds: 3),
    super.key,
  });

  final String message;
  final NotificationType type;
  final Duration duration;

  @override
  State<Toast> createState() => _ToastState();
}

class _ToastState extends State<Toast> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 300));
    _animation = Tween<double>(begin: 0, end: 1).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));

    _controller.forward();

    Future.delayed(widget.duration, () {
      if (mounted) {
        _controller.reverse().then((_) {
          if (mounted) Navigator.pop(context);
        });
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = {
      NotificationType.success: const Color(0xFF10B981),
      NotificationType.error: AppColors.danger,
      NotificationType.warning: const Color(0xFFF59E0B),
      NotificationType.info: AppColors.skyBlue,
    };

    final icons = {
      NotificationType.success: Icons.check_circle,
      NotificationType.error: Icons.error,
      NotificationType.warning: Icons.warning_amber,
      NotificationType.info: Icons.info,
    };

    final color = colors[widget.type]!;
    final icon = icons[widget.type]!;

    return ScaleTransition(
      scale: _animation,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [BoxShadow(color: color.withValues(alpha: 0.3), blurRadius: 12, offset: const Offset(0, 4))],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: Colors.white, size: 20),
            const SizedBox(width: 12),
            Expanded(child: Text(widget.message, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500))),
          ],
        ),
      ),
    );
  }
}

void showToast(BuildContext context, String message, {NotificationType type = NotificationType.info}) {
  showDialog(
    context: context,
    builder: (_) => Toast(message: message, type: type),
    barrierDismissible: true,
    barrierColor: Colors.transparent,
  );
}
