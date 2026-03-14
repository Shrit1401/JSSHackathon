import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class TrafficMetricRow extends StatelessWidget {
  final String label;
  final String value;
  final String? baseline;
  final Color? valueColor;

  const TrafficMetricRow({
    super.key,
    required this.label,
    required this.value,
    this.baseline,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 9),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 11,
              
              letterSpacing: 0.5,
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                value,
                style: TextStyle(
                  color: valueColor ?? AppColors.textPrimary,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  
                ),
              ),
              if (baseline != null)
                Text(
                  'base: $baseline',
                  style: const TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 10,
                    
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
