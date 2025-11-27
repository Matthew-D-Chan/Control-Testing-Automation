import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import './ChatWindow.css';

export function ChatWindow({ messages, onSend, isTyping = false }) {
  return (
    <div className="chat-window">
      <MessageList messages={messages} isTyping={isTyping} />
      <ChatInput onSend={onSend} disabled={isTyping} />
    </div>
  );
}

