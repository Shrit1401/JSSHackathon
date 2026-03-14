import 'package:flutter/material.dart';

class AppColors {
  // Base — pure blacks
  static const Color background = Color(0xFF0A0A0A);
  static const Color surface = Color(0xFF111111);
  static const Color surfaceLight = Color(0xFF1A1A1A);
  static const Color surfaceBorder = Color(0xFF222222);

  // Accent — teal/cyan
  static const Color accent = Color(0xFF00E5A0);
  static const Color accentDim = Color(0xFF00B07A);
  static const Color accentGlow = Color(0xFF00FFB0);

  // Status
  static const Color safe = Color(0xFF00E676);
  static const Color warning = Color(0xFFFFB300);
  static const Color danger = Color(0xFFFF3D3D);

  // Node badge colors
  static const Color nodeOrange = Color(0xFFFF8C00);
  static const Color nodeTeal = Color(0xFF00BFA5);

  // Text
  static const Color textPrimary = Color(0xFFEEEEEE);
  static const Color textSecondary = Color(0xFF555555);
  static const Color textMuted = Color(0xFF333333);

  // Code / mono
  static const Color codeFg = Color(0xFF00E5A0);

  // Danger theme accent (when systems not secure)
  static const Color dangerAccent = Color(0xFFFF3D3D);
  static const Color dangerAccentDim = Color(0xFFCC3131);
  static const Color dangerAccentGlow = Color(0xFFFF6B6B);
}

class AppTheme {
  static ThemeData get dark => _buildTheme(
        accent: AppColors.accent,
        accentDim: AppColors.accentDim,
      );

  /// Red theme when not all systems secure.
  static ThemeData get danger => _buildTheme(
        accent: AppColors.dangerAccent,
        accentDim: AppColors.dangerAccentDim,
      );

  static ThemeData _buildTheme({
    required Color accent,
    required Color accentDim,
  }) => ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.dark(
          surface: AppColors.surface,
          primary: accent,
          secondary: accentDim,
          onPrimary: AppColors.background,
          onSurface: AppColors.textPrimary,
          error: AppColors.danger,
        ),
        scaffoldBackgroundColor: AppColors.background,
        appBarTheme: const AppBarTheme(
          backgroundColor: AppColors.background,
          foregroundColor: AppColors.textPrimary,
          elevation: 0,
          centerTitle: false,
          surfaceTintColor: Colors.transparent,
          titleTextStyle: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 16,
            fontWeight: FontWeight.w600,
            letterSpacing: 1.2,
          ),
        ),
        cardTheme: CardThemeData(
          color: AppColors.surface,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
            side: const BorderSide(color: AppColors.surfaceBorder),
          ),
        ),
        bottomNavigationBarTheme: BottomNavigationBarThemeData(
          backgroundColor: AppColors.surface,
          selectedItemColor: accent,
          unselectedItemColor: AppColors.textSecondary,
          type: BottomNavigationBarType.fixed,
          elevation: 0,
        ),
        textTheme: TextTheme(
          bodyLarge: const TextStyle(color: AppColors.textPrimary),
          bodyMedium: const TextStyle(color: AppColors.textPrimary),
          bodySmall: const TextStyle(color: AppColors.textSecondary),
          titleLarge: const TextStyle(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.bold,
              letterSpacing: 0.8),
          titleMedium: const TextStyle(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w600),
          titleSmall: const TextStyle(color: AppColors.textSecondary),
          labelLarge: TextStyle(
              color: accent,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.5),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: AppColors.surfaceLight,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(6),
            borderSide: const BorderSide(color: AppColors.surfaceBorder),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(6),
            borderSide: const BorderSide(color: AppColors.surfaceBorder),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(6),
            borderSide: BorderSide(color: accent, width: 1),
          ),
          hintStyle: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 13),
        ),
        dividerColor: AppColors.surfaceBorder,
        iconTheme: const IconThemeData(color: AppColors.textSecondary),
      );
}
