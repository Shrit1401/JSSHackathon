class AppConfig {
  /// Backend API base URL (deployed Sentinel on Render).
  static const String baseUrl = 'https://jsshackathon.onrender.com';
  /// Polling interval for alerts/devices/overview. Shorter = faster to see new alerts after simulate-attack.
  static const int refreshIntervalSeconds = 5;
  static bool useMockData = false;

  /// Hack Club AI — for assistant chat. Use dart-define or env in production.
  static const String hackClubAiBaseUrl = 'https://ai.hackclub.com/proxy/v1';
  static const String hackClubAiApiKey =
      'sk-hc-v1-2f31728e3a5d4a729dc4622d94a84ec3fbb60f5881e6400190ab64158160c828';
}
