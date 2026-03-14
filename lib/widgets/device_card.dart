import 'package:flutter/material.dart';
import '../models/device.dart';
import '../theme/app_theme.dart';

class DeviceCard extends StatelessWidget {
  final Device device;
  final VoidCallback onTap;

  const DeviceCard({super.key, required this.device, required this.onTap});

  Color get _riskColor => switch (device.riskLevel) {
        RiskLevel.safe => AppColors.safe,
        RiskLevel.low => AppColors.warning,
        RiskLevel.medium => AppColors.warning,
        RiskLevel.high => AppColors.danger,
        RiskLevel.compromised => AppColors.danger,
      };

  String get _riskLabel => switch (device.riskLevel) {
        RiskLevel.safe => 'SAFE',
        RiskLevel.low => 'LOW',
        RiskLevel.medium => 'MED',
        RiskLevel.high => 'HIGH',
        RiskLevel.compromised => 'CRIT',
      };

  @override
  Widget build(BuildContext context) {
    final primary = Theme.of(context).colorScheme.primary;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: AppColors.surfaceBorder),
        ),
        child: Row(
          children: [
            // Node indicator
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _riskColor,
                boxShadow: [
                  BoxShadow(
                    color: _riskColor.withValues(alpha: 0.5),
                    blurRadius: 6,
                    spreadRadius: 1,
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        device.name,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          
                          letterSpacing: 0.3,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '// ${device.type}',
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 11,
                          
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 3),
                  Text(
                    device.ip,
                    style: TextStyle(
                      color: primary,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  device.trustScore.toStringAsFixed(0),
                  style: TextStyle(
                    color: _riskColor,
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    
                  ),
                ),
                const SizedBox(height: 2),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: _riskColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(3),
                    border: Border.all(color: _riskColor.withValues(alpha: 0.35)),
                  ),
                  child: Text(
                    _riskLabel,
                    style: TextStyle(
                      color: _riskColor,
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 0.8,
                      
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(width: 6),
            const Icon(Icons.chevron_right, color: AppColors.textMuted, size: 16),
          ],
        ),
      ),
    );
  }
}
