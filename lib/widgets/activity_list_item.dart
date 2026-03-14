import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/overview_stats.dart';
import '../theme/app_theme.dart';

class ActivityListItem extends StatelessWidget {
  final ActivityItem item;

  const ActivityListItem({super.key, required this.item});

  @override
  Widget build(BuildContext context) {
    final primary = Theme.of(context).colorScheme.primary;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '>',
            style: TextStyle(
              color: primary,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.description,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 12,
                    height: 1.4,
                    
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  DateFormat('yyyy-MM-dd HH:mm').format(item.timestamp.toLocal()),
                  style: const TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 10,
                    
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
