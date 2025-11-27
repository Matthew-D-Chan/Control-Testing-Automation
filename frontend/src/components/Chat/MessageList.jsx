import { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from '../common/Loader';
import './MessageList.css';

export function MessageList({ messages, isTyping = false }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  return (
    <div className="message-list">
      <div className="message-list-content">
        {messages.length === 0 ? (
          <div className="message-list-empty">
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          messages.map((message) => (
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

