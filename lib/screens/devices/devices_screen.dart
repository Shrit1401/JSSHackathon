import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/devices_provider.dart';
import '../../theme/app_theme.dart';
import '../../widgets/device_card.dart';
import 'device_detail_screen.dart';

class DevicesScreen extends StatelessWidget {
  const DevicesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<DevicesProvider>(
      builder: (context, provider, _) {
        return RefreshIndicator(
          onRefresh: provider.load,
          color: Theme.of(context).colorScheme.primary,
          backgroundColor: AppColors.surface,
          child: CustomScrollView(
            slivers: [
              _DevicesAppBar(provider: provider),
              if (provider.isLoading && provider.devices.isEmpty)
                SliverFillRemaining(
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const _NodeLoader(),
                        const SizedBox(height: 16),
                        Text(
                          'Loading devices…',
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 13,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'First load may take ~25s. Stuck? Pull down to retry.',
                          style: TextStyle(
                            color: AppColors.textSecondary.withValues(alpha: 0.8),
                            fontSize: 11,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                )
              else if (provider.error != null && provider.devices.isEmpty)
                SliverFillRemaining(
                  child: _ErrorState(onRetry: provider.load, message: provider.error!),
                )
              else
                SliverPadding(
                  padding: const EdgeInsets.only(top: 6, bottom: 24),
                  sliver: SliverList.builder(
                    itemCount: provider.devices.length,
                    itemBuilder: (context, i) {
                      final device = provider.devices[i];
                      return DeviceCard(
                        device: device,
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => DeviceDetailScreen(
                              deviceId: device.id,
                              device: device,
                            ),
                          ),
                        ),
                      );
                    },
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}

class _DevicesAppBar extends StatelessWidget {
  final DevicesProvider provider;

  const _DevicesAppBar({required this.provider});

  @override
  Widget build(BuildContext context) {
    final primary = Theme.of(context).colorScheme.primary;
    return SliverAppBar(
      floating: true,
      snap: true,
      backgroundColor: AppColors.background,
      elevation: 0,
      toolbarHeight: 52,
      titleSpacing: 16,
      title: Row(
        children: [
          const Text(
            'NODES',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 14,
              fontWeight: FontWeight.w700,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(width: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
            decoration: BoxDecoration(
              color: primary.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: primary.withValues(alpha: 0.3)),
            ),
            child: Text(
              '${provider.devices.length}',
              style: TextStyle(
                color: primary,
                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(1),
        child: Container(height: 1, color: AppColors.surfaceBorder),
      ),
    );
  }
}

class _NodeLoader extends StatefulWidget {
  const _NodeLoader();

  @override
  State<_NodeLoader> createState() => _NodeLoaderState();
}

class _NodeLoaderState extends State<_NodeLoader> with SingleTickerProviderStateMixin {
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
    final primary = Theme.of(context).colorScheme.primary;
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
              color: primary.withValues(alpha: opacity),
            ),
          );
        }),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorState({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final primary = Theme.of(context).colorScheme.primary;
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
                border: Border.all(color: primary),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text('RETRY', style: TextStyle(color: primary, fontSize: 12, letterSpacing: 1, fontFamily: 'monospace')),
            ),
          ),
        ],
      ),
    );
  }
}
