export function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const timestamp = new Date(message.createdAt).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });

  return (
    <div className={`message-bubble message-bubble-${message.role}`}>
      <div className="message-content">
        <div className="message-text">{message.content}</div>
        <div className="message-timestamp">{timestamp}</div>
      </div>
    </div>
  );
}

