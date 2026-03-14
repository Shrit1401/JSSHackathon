import 'package:flutter/material.dart';
import '../models/chat_message.dart';
import '../theme/app_theme.dart';

class ChatBubble extends StatefulWidget {
  final ChatMessage message;

  const ChatBubble({super.key, required this.message});

  @override
  State<ChatBubble> createState() => _ChatBubbleState();
}

class _ChatBubbleState extends State<ChatBubble> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller =
        AnimationController(vsync: this, duration: const Duration(milliseconds: 600))..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isUser = widget.message.sender == MessageSender.user;

    return Padding(
      padding: EdgeInsets.only(
        bottom: 10,
        left: isUser ? 48 : 0,
        right: isUser ? 0 : 48,
      ),
      child: Column(
        crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          // prefix label
          Padding(
            padding: const EdgeInsets.only(bottom: 3),
            child: Text(
              isUser ? '// you' : '// sys',
              style: TextStyle(
                color: isUser ? AppColors.textSecondary : Theme.of(context).colorScheme.secondary,
                fontSize: 9,
                
                letterSpacing: 0.8,
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: isUser ? AppColors.surfaceLight : AppColors.surface,
              borderRadius: BorderRadius.circular(6),
              border: Border.all(
                color: isUser
                    ? AppColors.surfaceBorder
                    : Theme.of(context).colorScheme.primary.withValues(alpha: 0.2),
              ),
            ),
            child: widget.message.isLoading
                ? _LoadingDots(controller: _controller)
                : Text(
                    widget.message.text,
                    style: TextStyle(
                      color: isUser ? AppColors.textPrimary : AppColors.textPrimary,
                      fontSize: 13,
                      height: 1.5,
                      
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}

class _LoadingDots extends AnimatedWidget {
  const _LoadingDots({required AnimationController controller})
      : super(listenable: controller);

  @override
  Widget build(BuildContext context) {
    final animation = listenable as AnimationController;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: List.generate(3, (i) {
        final delay = i * 0.33;
        final opacity = ((animation.value + delay) % 1.0 < 0.5) ? 1.0 : 0.2;
        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 2),
          width: 6,
          height: 6,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primary.withValues(alpha: opacity),
            shape: BoxShape.circle,
          ),
        );
      }),
    );
  }
}
