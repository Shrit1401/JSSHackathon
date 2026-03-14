import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Displays the current trust score as a horizontal bar with score label.
/// (The real API does not provide historical trust score data.)
class TrustScoreChart extends StatelessWidget {
  final double trustScore;

  const TrustScoreChart({super.key, required this.trustScore});

  Color get _color {
    if (trustScore >= 70) return AppColors.safe;
    if (trustScore >= 40) return AppColors.warning;
    return AppColors.danger;
  }

  @override
  Widget build(BuildContext context) {
    final raw = trustScore.isNaN || trustScore.isInfinite ? 0.0 : trustScore;
    final progress = (raw / 100).clamp(0.0, 1.0);
    final safeFactor = progress.isNaN ? 0.0 : progress;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Current Trust',
              style: const TextStyle(color: AppColors.textSecondary, fontSize: 11),
            ),
            Text(
              '${raw.toStringAsFixed(0)} / 100',
              style: TextStyle(
                color: _color,
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        ClipRRect(
          borderRadius: BorderRadius.circular(3),
          child: Stack(
            children: [
              Container(height: 8, color: AppColors.surfaceBorder),
              FractionallySizedBox(
                widthFactor: safeFactor,
                child: Container(
                  height: 8,
                  decoration: BoxDecoration(
                    color: _color,
                    boxShadow: [
                      BoxShadow(color: _color.withValues(alpha: 0.4), blurRadius: 6),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
