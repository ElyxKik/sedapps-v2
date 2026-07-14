import 'package:flutter/material.dart';

import '../core/theme.dart';

class ConfirmDialog extends StatelessWidget {
  const ConfirmDialog({
    required this.title,
    required this.message,
    required this.onConfirm,
    this.onCancel,
    this.confirmText = 'Confirmer',
    this.cancelText = 'Annuler',
    this.isDangerous = false,
    super.key,
  });

  final String title;
  final String message;
  final VoidCallback onConfirm;
  final VoidCallback? onCancel;
  final String confirmText;
  final String cancelText;
  final bool isDangerous;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(
          onPressed: () {
            Navigator.pop(context);
            onCancel?.call();
          },
          child: Text(cancelText),
        ),
        FilledButton(
          style: FilledButton.styleFrom(
            backgroundColor: isDangerous ? AppColors.danger : AppColors.skyBlue,
          ),
          onPressed: () {
            Navigator.pop(context);
            onConfirm();
          },
          child: Text(confirmText),
        ),
      ],
    );
  }
}

class InputDialog extends StatefulWidget {
  const InputDialog({
    required this.title,
    required this.label,
    required this.onSubmit,
    this.initialValue = '',
    this.hintText = '',
    this.maxLines = 1,
    super.key,
  });

  final String title;
  final String label;
  final String initialValue;
  final String hintText;
  final int maxLines;
  final Function(String) onSubmit;

  @override
  State<InputDialog> createState() => _InputDialogState();
}

class _InputDialogState extends State<InputDialog> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialValue);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.title),
      content: TextField(
        controller: _controller,
        decoration: InputDecoration(
          labelText: widget.label,
          hintText: widget.hintText,
        ),
        maxLines: widget.maxLines,
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Annuler'),
        ),
        FilledButton(
          onPressed: () {
            Navigator.pop(context);
            widget.onSubmit(_controller.text);
          },
          child: const Text('Valider'),
        ),
      ],
    );
  }
}

class SuccessDialog extends StatelessWidget {
  const SuccessDialog({
    required this.title,
    required this.message,
    this.onClose,
    super.key,
  });

  final String title;
  final String message;
  final VoidCallback? onClose;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              color: const Color(0xFF10B981).withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(30),
            ),
            child: const Icon(Icons.check, color: Color(0xFF10B981), size: 32),
          ),
          const SizedBox(height: 16),
          Text(title, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          Text(message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.textSecondary)),
          const SizedBox(height: 20),
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              onClose?.call();
            },
            child: const Text('Fermer'),
          ),
        ],
      ),
    );
  }
}

class ErrorDialog extends StatelessWidget {
  const ErrorDialog({
    required this.title,
    required this.message,
    this.onClose,
    super.key,
  });

  final String title;
  final String message;
  final VoidCallback? onClose;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              color: AppColors.danger.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(30),
            ),
            child: const Icon(Icons.error_outline,
                color: AppColors.danger, size: 32),
          ),
          const SizedBox(height: 16),
          Text(title, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          Text(message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.textSecondary)),
          const SizedBox(height: 20),
          FilledButton(
            onPressed: () {
              Navigator.pop(context);
              onClose?.call();
            },
            child: const Text('Fermer'),
          ),
        ],
      ),
    );
  }
}

void showConfirmDialog(
  BuildContext context, {
  required String title,
  required String message,
  required VoidCallback onConfirm,
  VoidCallback? onCancel,
  String confirmText = 'Confirmer',
  String cancelText = 'Annuler',
  bool isDangerous = false,
}) {
  showDialog(
    context: context,
    builder: (_) => ConfirmDialog(
      title: title,
      message: message,
      onConfirm: onConfirm,
      onCancel: onCancel,
      confirmText: confirmText,
      cancelText: cancelText,
      isDangerous: isDangerous,
    ),
  );
}

void showInputDialog(
  BuildContext context, {
  required String title,
  required String label,
  required Function(String) onSubmit,
  String initialValue = '',
  String hintText = '',
  int maxLines = 1,
}) {
  showDialog(
    context: context,
    builder: (_) => InputDialog(
      title: title,
      label: label,
      onSubmit: onSubmit,
      initialValue: initialValue,
      hintText: hintText,
      maxLines: maxLines,
    ),
  );
}

void showSuccessDialog(
  BuildContext context, {
  required String title,
  required String message,
  VoidCallback? onClose,
}) {
  showDialog(
    context: context,
    builder: (_) => SuccessDialog(
      title: title,
      message: message,
      onClose: onClose,
    ),
  );
}

void showErrorDialog(
  BuildContext context, {
  required String title,
  required String message,
  VoidCallback? onClose,
}) {
  showDialog(
    context: context,
    builder: (_) => ErrorDialog(
      title: title,
      message: message,
      onClose: onClose,
    ),
  );
}
