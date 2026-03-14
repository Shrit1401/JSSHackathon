import 'dart:math';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class NetworkTrustGauge extends StatelessWidget {
  final double score;

  const NetworkTrustGauge({super.key, required this.score});

  Color get _color {
    if (score >= 70) return AppColors.safe;
    if (score >= 40) return AppColors.warning;
    return AppColors.danger;
  }

  String get _status {
    if (score >= 70) return 'HEALTHY';
    if (score >= 40) return 'MODERATE';
    return 'CRITICAL';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.surfaceBorder),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'TRUST_SCORE',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 10,
                  letterSpacing: 1.5,
                  
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _color.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: _color.withValues(alpha: 0.3)),
                ),
                child: Text(
                  _status,
                  style: TextStyle(
                    color: _color,
                    fontSize: 9,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.2,
                    
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: 200,
            height: 120,
            child: CustomPaint(
              painter: _GaugePainter(score: score, color: _color),
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.only(top: 44),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        score.toStringAsFixed(0),
                        style: TextStyle(
                          color: _color,
                          fontSize: 40,
                          fontWeight: FontWeight.bold,
                          height: 1,
                          
                        ),
                      ),
                      Text(
                        '/ 100',
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 11,
                          
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          // Tick marks
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: ['0', '25', '50', '75', '100'].map((v) => Text(
              v,
              style: const TextStyle(
                color: AppColors.textMuted,
                fontSize: 9,
                
              ),
            )).toList(),
          ),
        ],
      ),
    );
  }
}

class _GaugePainter extends CustomPainter {
  final double score;
  final Color color;

  _GaugePainter({required this.score, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height);
    final radius = size.width / 2 - 10;

    // Track (segmented dots style like reference)
    final trackPaint = Paint()
      ..color = AppColors.surfaceBorder
      ..style = PaintingStyle.stroke
      ..strokeWidth = 10
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      pi,
      pi,
      false,
      trackPaint,
    );

    // Glow layer
    if (score > 0) {
      final progress = (score / 100).clamp(0.0, 1.0);
      final glowPaint = Paint()
        ..color = color.withValues(alpha: 0.15)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 18
        ..strokeCap = StrokeCap.round
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 6);

      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        pi,
        pi * progress,
        false,
        glowPaint,
      );

      // Value arc
      final valuePaint = Paint()
        ..color = color
        ..style = PaintingStyle.stroke
        ..strokeWidth = 10
        ..strokeCap = StrokeCap.round;

      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        pi,
        pi * progress,
        false,
        valuePaint,
      );

      // End dot
      final endAngle = pi + pi * progress;
      final dotX = center.dx + radius * cos(endAngle);
      final dotY = center.dy + radius * sin(endAngle);
      canvas.drawCircle(
        Offset(dotX, dotY),
        5,
        Paint()..color = Colors.white.withValues(alpha: 0.9),
      );
    }
  }

  @override
  bool shouldRepaint(_GaugePainter old) =>
      old.score != score || old.color != color;
}
