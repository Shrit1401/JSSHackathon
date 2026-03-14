import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'config/app_router.dart';
import 'theme/app_theme.dart';
import 'providers/overview_provider.dart';
import 'providers/devices_provider.dart';
import 'providers/alerts_provider.dart';
import 'providers/assistant_provider.dart';
import 'providers/network_map_provider.dart';
import 'screens/main_shell.dart';
import 'services/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const IoTTrustMonitorApp());
  // Init notifications after app is running so we never block the first frame (fixes white screen on web/emulator).
  if (!kIsWeb) {
    NotificationService().initialize().catchError((e, _) {
      if (kDebugMode) debugPrint('NotificationService init: $e');
    });
    NotificationService().startHealthMonitor();
  }
}

class IoTTrustMonitorApp extends StatelessWidget {
  const IoTTrustMonitorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => OverviewProvider()),
        ChangeNotifierProvider(create: (_) => DevicesProvider()),
        ChangeNotifierProvider(create: (_) => AlertsProvider()),
        ChangeNotifierProvider(create: (_) => AssistantProvider()),
        ChangeNotifierProvider(create: (_) => NetworkMapProvider()),
      ],
      child: Consumer<OverviewProvider>(
        builder: (context, overview, _) {
          final isAllSecure = overview.stats == null ||
              (overview.stats!.highRiskDevices == 0 &&
                  overview.stats!.suspiciousDevices == 0);
          return MaterialApp(
            title: 'Sentinel',
            theme: isAllSecure ? AppTheme.dark : AppTheme.danger,
            debugShowCheckedModeBanner: false,
            navigatorKey: AppRouter.navigatorKey,
            home: const MainShell(),
          );
        },
      ),
    );
  }
}
