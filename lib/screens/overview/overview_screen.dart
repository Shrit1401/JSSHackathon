import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/overview_provider.dart';
import '../../services/api_service.dart';
import '../../theme/app_theme.dart';
import '../../widgets/network_trust_gauge.dart';
import '../../widgets/activity_list_item.dart';

class OverviewScreen extends StatelessWidget {
  const OverviewScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<OverviewProvider>(
      builder: (context, provider, _) {
        return RefreshIndicator(
          onRefresh: provider.load,
          color: Theme.of(context).colorScheme.primary,
          backgroundColor: AppColors.surface,
          child: CustomScrollView(
            slivers: [
              _CyberAppBar(),
              if (provider.isLoading && provider.stats == null)
                const SliverFillRemaining(
                  child: Center(
                    child: _PulseLoader(),
                  ),
                )
              else if (provider.error != null && provider.stats == null)
                SliverFillRemaining(
                  child: _ErrorState(onRetry: provider.load, message: provider.error!),
                )
              else if (provider.stats != null)
                _OverviewContent(provider: provider),
            ],
          ),
        );
      },
    );
  }
}

class _CyberAppBar extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SliverAppBar(
      floating: true,
      snap: true,
      backgroundColor: AppColors.background,
      elevation: 0,
      titleSpacing: 16,
      toolbarHeight: 52,
      title: Row(
        children: [
          Image.asset(
            'logo.png',
            height: 32,
            fit: BoxFit.contain,
            errorBuilder: (_, __, ___) => Icon(
              Icons.shield_outlined,
              color: Theme.of(context).colorScheme.primary,
              size: 28,
            ),
          ),
          const SizedBox(width: 10),
          Builder(
            builder: (context) => Text(
              'SENTINEL',
              style: TextStyle(
                color: Theme.of(context).colorScheme.primary,
                fontSize: 14,
                fontWeight: FontWeight.w700,
                letterSpacing: 2,
              ),
            ),
          ),
          const Spacer(),
          _LivePulse(),
        ],
      ),
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(1),
        child: Container(height: 1, color: AppColors.surfaceBorder),
      ),
    );
  }
}

class _LivePulse extends StatefulWidget {
  @override
  State<_LivePulse> createState() => _LivePulseState();
}

class _LivePulseState extends State<_LivePulse> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  bool _healthy = false;
  Timer? _healthTimer;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(seconds: 2))..repeat();
    _checkHealth();
    _healthTimer = Timer.periodic(const Duration(seconds: 30), (_) => _checkHealth());
  }

  Future<void> _checkHealth() async {
    final ok = await ApiService().checkHealth();
    if (mounted && _healthy != ok) {
      setState(() => _healthy = ok);
    }
  }

  @override
  void dispose() {
    _healthTimer?.cancel();
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final color = _healthy ? Theme.of(context).colorScheme.primary : AppColors.textSecondary;
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, __) => Row(
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color.withValues(alpha: _healthy
                  ? (0.4 + 0.6 * ((_ctrl.value * 2) % 1.0 < 0.5 ? _ctrl.value * 2 : 2 - _ctrl.value * 2))
                  : 0.5),
            ),
          ),
          const SizedBox(width: 6),
          Text(
            _healthy ? 'LIVE' : 'OFFLINE',
            style: TextStyle(
              color: color,
              fontSize: 9,
              letterSpacing: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}

class _OverviewContent extends StatelessWidget {
  final OverviewProvider provider;
  const _OverviewContent({required this.provider});

  @override
  Widget build(BuildContext context) {
    final stats = provider.stats!;
    final isAllSafe = stats.highRiskDevices == 0 && stats.suspiciousDevices == 0;
    final statusColor = isAllSafe ? AppColors.safe : AppColors.danger;
    final statusText = isAllSafe ? 'ALL_SYSTEMS_SECURE' : 'THREATS_DETECTED';
    final threatCount = stats.highRiskDevices + stats.suspiciousDevices;

    return SliverPadding(
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 24),
      sliver: SliverList(
        delegate: SliverChildListDelegate([

          // ── Status Banner ─────────────────────────────────────────────
          _StatusBanner(
            color: statusColor,
            isAllSafe: isAllSafe,
            title: statusText,
            subtitle: isAllSafe
                ? '// network operating normally'
                : '// $threatCount device${threatCount > 1 ? 's' : ''} require attention',
          ),
          const SizedBox(height: 12),

          // ── Stat Row ─────────────────────────────────────────────────
          Row(
            children: [
              _StatChip(label: 'TOTAL', value: stats.totalDevices.toString(), color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: 8),
              _StatChip(label: 'SAFE', value: stats.safeDevices.toString(), color: AppColors.safe),
              const SizedBox(width: 8),
              _StatChip(
                label: 'WARN',
                value: stats.suspiciousDevices.toString(),
                color: stats.suspiciousDevices > 0 ? AppColors.warning : AppColors.textSecondary,
              ),
              const SizedBox(width: 8),
              _StatChip(
                label: 'CRIT',
                value: stats.highRiskDevices.toString(),
                color: stats.highRiskDevices > 0 ? AppColors.danger : AppColors.textSecondary,
              ),
            ],
          ),
          const SizedBox(height: 14),

          // ── Trust Gauge ───────────────────────────────────────────────
          NetworkTrustGauge(score: stats.networkTrustScore),
          const SizedBox(height: 18),

          // ── Activity Section ──────────────────────────────────────────
          Row(
            children: [
              Container(width: 2, height: 12, color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: 8),
              const Text(
                'RECENT_ACTIVITY',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.5,
                  
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Container(
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.surfaceBorder),
            ),
            child: ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              padding: EdgeInsets.zero,
              itemCount: stats.recentActivity.length,
              separatorBuilder: (_, __) =>
                  const Divider(color: AppColors.surfaceBorder, height: 1),
              itemBuilder: (_, i) =>
                  ActivityListItem(item: stats.recentActivity[i]),
            ),
          ),
        ]),
      ),
    );
  }
}

// ── Status Banner ──────────────────────────────────────────────────────────────

class _StatusBanner extends StatelessWidget {
  final Color color;
  final bool isAllSafe;
  final String title;
  final String subtitle;

  const _StatusBanner({
    required this.color,
    required this.isAllSafe,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Icon(
              isAllSafe ? Icons.check_rounded : Icons.gpp_bad_outlined,
              color: color,
              size: 18,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: color,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.8,
                    
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11,
                    
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: color.withValues(alpha: 0.3)),
            ),
            child: Text(
              isAllSafe ? 'OK' : 'ERR',
              style: TextStyle(
                color: color,
                fontSize: 10,
                fontWeight: FontWeight.w700,
                letterSpacing: 1,
                
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Stat Chip ──────────────────────────────────────────────────────────────────

class _StatChip extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _StatChip({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: color.withValues(alpha: 0.25)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              value,
              style: TextStyle(
                color: color,
                fontSize: 20,
                fontWeight: FontWeight.bold,
                height: 1,
                
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 9,
                letterSpacing: 0.8,
                
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Shared helpers ─────────────────────────────────────────────────────────────

class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorState({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('ERR', style: TextStyle(color: AppColors.danger, fontSize: 32, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
          const SizedBox(height: 8),
          Text(message, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12, fontFamily: 'monospace')),
          const SizedBox(height: 16),
          GestureDetector(
            onTap: onRetry,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                border: Border.all(color: Theme.of(context).colorScheme.primary),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text('RETRY', style: TextStyle(color: Theme.of(context).colorScheme.primary, fontSize: 12, letterSpacing: 1, fontFamily: 'monospace')),
            ),
          ),
        ],
      ),
    );
  }
}

class _PulseLoader extends StatefulWidget {
  const _PulseLoader();

  @override
  State<_PulseLoader> createState() => _PulseLoaderState();
}

class _PulseLoaderState extends State<_PulseLoader> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 800))..repeat();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, __) => Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(3, (i) {
          final delay = i * 0.33;
          final opacity = (((_ctrl.value + delay) % 1.0) < 0.5) ? 1.0 : 0.2;
          return Container(
            margin: const EdgeInsets.symmetric(horizontal: 3),
            width: 6,
            height: 6,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Theme.of(context).colorScheme.primary.withValues(alpha: opacity),
            ),
          );
        }),
      ),
    );
  }
}
