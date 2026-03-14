import 'dart:ui' as ui;

import 'package:flutter/material.dart';

/// Simple line chart for trust or traffic history. Draws a smooth curved line
/// from [values] (left to right) using cubic interpolation.
class SimpleLineChart extends StatelessWidget {
  final List<double> values;
  final Color? lineColor;
  final double height;

  const SimpleLineChart({
    super.key,
    required this.values,
    this.lineColor,
    this.height = 80,
  });

  @override
  Widget build(BuildContext context) {
    final color = lineColor ?? Theme.of(context).colorScheme.primary;
    final data = values.isEmpty
        ? <double>[0.0, 0.0]
        : values.length == 1
            ? [values[0], values[0]]
            : values;
    return SizedBox(
      height: height,
      width: double.infinity,
      child: CustomPaint(
        painter: _LineChartPainter(
          values: data,
          lineColor: color,
        ),
      ),
    );
  }
}

class _LineChartPainter extends CustomPainter {
  final List<double> values;
  final Color lineColor;

  _LineChartPainter({required this.values, required this.lineColor});

  @override
  void paint(Canvas canvas, Size size) {
    if (values.length < 2) return;
    final minV = values.reduce((a, b) => a < b ? a : b);
    final maxV = values.reduce((a, b) => a > b ? a : b);
    final range = (maxV - minV).clamp(1e-6, double.infinity);
    final n = values.length;
    final stepX = (size.width - 1) / (n - 1);
    final h = size.height - 2;

    double xAt(int i) => i * stepX;
    double yAt(int i) => size.height - ((values[i] - minV) / range) * h - 1;

    final path = ui.Path();
    path.moveTo(xAt(0), yAt(0));

    for (var i = 0; i < n - 1; i++) {
      final x0 = xAt(i);
      final y0 = yAt(i);
      final x1 = xAt(i + 1);
      final y1 = yAt(i + 1);
      final prevX = i > 0 ? xAt(i - 1) : x0;
      final prevY = i > 0 ? yAt(i - 1) : y0;
      final nextX = i + 2 < n ? xAt(i + 2) : x1;
      final nextY = i + 2 < n ? yAt(i + 2) : y1;
      // Smooth cubic: control points for a Catmull-Rom–like curve
      final tension = 0.25;
      final cp1x = x0 + (x1 - prevX) * tension;
      final cp1y = y0 + (y1 - prevY) * tension;
      final cp2x = x1 - (nextX - x0) * tension;
      final cp2y = y1 - (nextY - y0) * tension;
      path.cubicTo(cp1x, cp1y, cp2x, cp2y, x1, y1);
    }

    final paint = Paint()
      ..color = lineColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant _LineChartPainter old) =>
      old.values != values || old.lineColor != lineColor;
}
