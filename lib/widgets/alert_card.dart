import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/alert.dart';
import '../theme/app_theme.dart';

class AlertCard extends StatelessWidget {
  final Alert alert;

  const AlertCard({super.key, required this.alert});

  Color get _severityColor => switch (alert.severity) {
        AlertSeverity.critical => AppColors.danger,
        AlertSeverity.high => AppColors.danger,
        AlertSeverity.medium => AppColors.warning,
        AlertSeverity.low => AppColors.textSecondary,
        AlertSeverity.info => AppColors.textMuted,
      };

  String get _severityLabel => switch (alert.severity) {
        AlertSeverity.critical => 'CRIT',
        AlertSeverity.high => 'HIGH',
        AlertSeverity.medium => 'MED',
        AlertSeverity.low => 'LOW',
        AlertSeverity.info => 'INFO',
      };

  String get _severityPrefix => switch (alert.severity) {
        AlertSeverity.critical => '[!!]',
        AlertSeverity.high => '[!]',
        AlertSeverity.medium => '[~]',
        AlertSeverity.low => '[i]',
        AlertSeverity.info => '[·]',
      };

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border(
          left: BorderSide(color: _severityColor, width: 2),
          right: BorderSide(color: AppColors.surfaceBorder),
          top: BorderSide(color: AppColors.surfaceBorder),
          bottom: BorderSide(color: AppColors.surfaceBorder),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 11, 14, 11),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  _severityPrefix,
                  style: TextStyle(
                    color: _severityColor,
                    fontSize: 11,
                    
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    alert.alertType.toUpperCase(),
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.5,
                      
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: _severityColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(3),
                    border: Border.all(color: _severityColor.withValues(alpha: 0.3)),
                  ),
                  child: Text(
                    _severityLabel,
                    style: TextStyle(
                      color: _severityColor,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.8,
                      
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              '> ${alert.deviceName}',
              style: TextStyle(
                color: Theme.of(context).colorScheme.primary,
                fontSize: 11,
                
              ),
            ),
            const SizedBox(height: 5),
            Text(
              alert.message,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
                height: 1.4,
                
              ),
            ),
            const SizedBox(height: 7),
            Text(
              DateFormat('yyyy-MM-dd HH:mm:ss').format(alert.timestamp.toLocal()),
              style: const TextStyle(
                color: AppColors.textMuted,
                fontSize: 10,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
