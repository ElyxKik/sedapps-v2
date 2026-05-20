import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mobile/src/widgets/animations.dart';
import 'package:mobile/src/widgets/dialogs.dart';
import 'package:mobile/src/widgets/notifications.dart';

void main() {
  group('Animations Tests', () {
    testWidgets('FadeInUp animates correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: FadeInUp(
              child: Container(width: 100, height: 100, color: Colors.blue),
            ),
          ),
        ),
      );

      expect(find.byType(FadeInUp), findsOneWidget);
      expect(find.byType(TweenAnimationBuilder), findsOneWidget);

      await tester.pumpAndSettle();
      expect(find.byType(Container), findsOneWidget);
    });

    testWidgets('ScaleIn animates correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ScaleIn(
              child: Container(width: 100, height: 100, color: Colors.red),
            ),
          ),
        ),
      );

      expect(find.byType(ScaleIn), findsOneWidget);
      await tester.pumpAndSettle();
    });

    testWidgets('SlideInLeft animates correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SlideInLeft(
              child: Container(width: 100, height: 100, color: Colors.green),
            ),
          ),
        ),
      );

      expect(find.byType(SlideInLeft), findsOneWidget);
      await tester.pumpAndSettle();
    });

    testWidgets('PulseAnimation pulses correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PulseAnimation(
              child: Container(width: 100, height: 100, color: Colors.yellow),
            ),
          ),
        ),
      );

      expect(find.byType(PulseAnimation), findsOneWidget);
      expect(find.byType(ScaleTransition), findsOneWidget);
    });
  });

  group('Dialogs Tests', () {
    testWidgets('ConfirmDialog displays correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ConfirmDialog(
              title: 'Test',
              message: 'Test message',
              onConfirm: () {},
            ),
          ),
        ),
      );

      expect(find.text('Test'), findsWidgets);
      expect(find.text('Test message'), findsOneWidget);
      expect(find.byType(AlertDialog), findsOneWidget);
    });

    testWidgets('SuccessDialog displays correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SuccessDialog(
              title: 'Succès',
              message: 'Opération réussie',
            ),
          ),
        ),
      );

      expect(find.text('Succès'), findsOneWidget);
      expect(find.text('Opération réussie'), findsOneWidget);
      expect(find.byIcon(Icons.check), findsOneWidget);
    });

    testWidgets('ErrorDialog displays correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ErrorDialog(
              title: 'Erreur',
              message: 'Une erreur est survenue',
            ),
          ),
        ),
      );

      expect(find.text('Erreur'), findsOneWidget);
      expect(find.text('Une erreur est survenue'), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
    });
  });

  group('Notifications Tests', () {
    testWidgets('Toast displays correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Toast(
              message: 'Test notification',
              type: NotificationType.success,
            ),
          ),
        ),
      );

      expect(find.text('Test notification'), findsOneWidget);
      expect(find.byType(Toast), findsOneWidget);
      expect(find.byIcon(Icons.check_circle), findsOneWidget);
    });

    testWidgets('Toast with error type', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Toast(
              message: 'Error message',
              type: NotificationType.error,
            ),
          ),
        ),
      );

      expect(find.text('Error message'), findsOneWidget);
      expect(find.byIcon(Icons.error), findsOneWidget);
    });

    testWidgets('Toast with warning type', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Toast(
              message: 'Warning message',
              type: NotificationType.warning,
            ),
          ),
        ),
      );

      expect(find.text('Warning message'), findsOneWidget);
      expect(find.byIcon(Icons.warning_amber), findsOneWidget);
    });
  });
}
