import { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from '../common/Loader';
export function MessageList({ messages, isTyping = false }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Ensure messages are sorted by createdAt to maintain chronological order
  // This is a safety net in case messages arrive out of order
  const sortedMessages = [...messages].sort((a, b) => {
    const dateA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
    const dateB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
    // If timestamps are equal, use id as tiebreaker for consistent ordering
    if (dateA === dateB) {
      return a.id.localeCompare(b.id);
    }
    return dateA - dateB;
  });

  return (
    <div className="message-list">
      <div className="message-list-content">
        {sortedMessages.length === 0 ? (
          <div className="message-list-empty">
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          sortedMessages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}
        {isTyping && (
          <div className="message-bubble message-bubble-assistant">
            <div className="message-content">
              <TypingIndicator />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

