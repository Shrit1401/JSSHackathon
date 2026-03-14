import 'package:flutter/foundation.dart';
import '../models/chat_message.dart';
import '../services/api_service.dart';

class AssistantProvider extends ChangeNotifier {
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;

  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get isLoading => _isLoading;

  AssistantProvider() {
    _messages.add(ChatMessage(
      id: 'welcome',
      text: 'Hello! I\'m your IoT security assistant. Ask me about device risks, alerts, or how to secure your network.',
      sender: MessageSender.assistant,
      timestamp: DateTime.now(),
    ));
  }

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    _messages.add(ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      text: text.trim(),
      sender: MessageSender.user,
      timestamp: DateTime.now(),
    ));

    final loadingId = '${DateTime.now().millisecondsSinceEpoch}_loading';
    _messages.add(ChatMessage(
      id: loadingId,
      text: '',
      sender: MessageSender.assistant,
      timestamp: DateTime.now(),
      isLoading: true,
    ));
    _isLoading = true;
    notifyListeners();

    try {
      final reply = await ApiService().sendAssistantMessage(text.trim());
      final idx = _messages.indexWhere((m) => m.id == loadingId);
      if (idx != -1) {
        _messages[idx] = ChatMessage(
          id: loadingId,
          text: reply,
          sender: MessageSender.assistant,
          timestamp: DateTime.now(),
        );
      }
    } catch (e) {
      final idx = _messages.indexWhere((m) => m.id == loadingId);
      if (idx != -1) {
        _messages[idx] = ChatMessage(
          id: loadingId,
          text: 'Sorry, I encountered an error. Please try again.',
          sender: MessageSender.assistant,
          timestamp: DateTime.now(),
        );
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}
