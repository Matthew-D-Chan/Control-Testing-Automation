export function Loader({ size = 'medium' }) {
  return (
    <div className={`loader loader-${size}`}>
      <div className="loader-spinner"></div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <span></span>
      <span></span>
      <span></span>
    </div>
  );
}

