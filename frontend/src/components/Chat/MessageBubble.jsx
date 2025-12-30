export function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  // Format timestamp for display
  // Handles UTC timestamps from backend and converts to local time
  const formatTimestamp = (date) => {
    if (!date) return '';
    const d = new Date(date);
    if (isNaN(d.getTime())) return '';
    
    // Use local time methods - JavaScript Date automatically converts UTC to local timezone
    const hours = d.getHours().toString().padStart(2, '0');
    const minutes = d.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
  };

  return (
    <div className={`message-bubble message-bubble-${message.role}`}>
      <div className="message-content">
        <div className="message-text">{message.content}</div>
        {message.createdAt && (
          <div className="message-timestamp">
            {formatTimestamp(message.createdAt)}
          </div>
        )}
      </div>
    </div>
  );
}

