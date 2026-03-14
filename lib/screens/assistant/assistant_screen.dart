import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/assistant_provider.dart';
import '../../theme/app_theme.dart';
import '../../widgets/chat_bubble.dart';

class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key});

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _send(AssistantProvider provider) {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    provider.sendMessage(text);
    _scrollToBottom();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final primary = Theme.of(context).colorScheme.primary;
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        titleSpacing: 16,
        toolbarHeight: 52,
        title: Row(
          children: [
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: primary.withValues(alpha: 0.3)),
              ),
              child: Icon(Icons.terminal_rounded, color: primary, size: 14),
            ),
            const SizedBox(width: 10),
            const Text(
              'SEC_SHELL',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 14,
                fontWeight: FontWeight.w700,
                letterSpacing: 2,
                
              ),
            ),
          ],
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: AppColors.surfaceBorder),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: Consumer<AssistantProvider>(
              builder: (context, provider, _) {
                WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
                return ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 14),
                  itemCount: provider.messages.length,
                  itemBuilder: (_, i) => ChatBubble(message: provider.messages[i]),
                );
              },
            ),
          ),
          _buildInputBar(context),
        ],
      ),
    );
  }

  Widget _buildInputBar(BuildContext context) {
    final primary = Theme.of(context).colorScheme.primary;
    return Container(
      padding: const EdgeInsets.fromLTRB(14, 8, 14, 0),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.surfaceBorder)),
      ),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            Text(
              '> ',
              style: TextStyle(
                color: primary,
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
            ),
            Expanded(
              child: Consumer<AssistantProvider>(
                builder: (context, provider, _) => TextField(
                  controller: _controller,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    
                    fontSize: 13,
                  ),
                  enabled: !provider.isLoading,
                  decoration: const InputDecoration(
                    hintText: 'query security data...',
                    hintStyle: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 13,
                      
                    ),
                    filled: false,
                    border: InputBorder.none,
                    enabledBorder: InputBorder.none,
                    focusedBorder: InputBorder.none,
                    contentPadding: EdgeInsets.symmetric(vertical: 12),
                  ),
                  onSubmitted: (_) {
                    if (!provider.isLoading) _send(provider);
                  },
                ),
              ),
            ),
            Consumer<AssistantProvider>(
              builder: (context, provider, _) => GestureDetector(
                onTap: provider.isLoading ? null : () => _send(provider),
                child: Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: provider.isLoading
                        ? AppColors.surfaceLight
                        : primary.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: provider.isLoading
                          ? AppColors.surfaceBorder
                          : primary.withValues(alpha: 0.4),
                    ),
                  ),
                  child: provider.isLoading
                      ? const Center(
                          child: SizedBox(
                            width: 14,
                            height: 14,
                            child: CircularProgressIndicator(
                              strokeWidth: 1.5,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        )
                      : Icon(Icons.arrow_forward_rounded,
                          color: primary, size: 16),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
