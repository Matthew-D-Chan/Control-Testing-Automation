import { useEffect, useRef } from 'react';
import cibcLogo from '../assets/cibc_logo.svg';
import { Loader } from './common/Loader';
export function HomeView({ sessions, onCreateSession, onSelectSession, onDeleteSession, isLoading }) {
  const sessionsRef = useRef(null);
  const heroRef = useRef(null);

  // Ensure sessions section is always visible when sessions exist
  useEffect(() => {
    if (sessionsRef.current) {
      sessionsRef.current.style.opacity = sessions.length > 0 ? 1 : 1;
    }
  }, [sessions.length]);

  const formatDate = (date) => {
    const dateObj = new Date(date);
    const now = new Date();
    const diffTime = Math.abs(now - dateObj);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    // If today, show time
    if (diffDays === 1) {
      return dateObj.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
      });
    }
    
    // If this week, show day name
    if (diffDays <= 7) {
      return dateObj.toLocaleDateString([], {
        weekday: 'long'
      });
    }
    
    // Otherwise show full date
    return dateObj.toLocaleDateString([], {
      month: 'short',
      day: 'numeric',
      year: dateObj.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };
  
  const formatSessionTitle = (date) => {
    const dateObj = new Date(date);
    return `Session from ${dateObj.toLocaleDateString([], {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    })}`;
  };

  return (
    <div className="home-view">
      <div ref={heroRef} className="home-hero">
        <div className="hero-content">
          <img src={cibcLogo} alt="Logo" className="hero-logo" />
          <h1 className="hero-title">Begin your interview here.</h1>
          <p className="hero-subtitle">Start a new session or continue an existing one</p>
          <button 
            className="hero-button"
            onClick={onCreateSession}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader size="small" />
                <span>Creating...</span>
              </>
            ) : (
              <>
                <span>+</span>
                <span>Start New Chat</span>
              </>
            )}
          </button>
        </div>
      </div>

      <div ref={sessionsRef} className="home-sessions">
        <div className="sessions-content">
          <h2 className="sessions-title">Previous Conversations</h2>
          {isLoading && sessions.length === 0 ? (
            <div className="sessions-loading">
              <Loader />
            </div>
          ) : sessions.length > 0 ? (
            <div className="sessions-list">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className="session-item"
                >
                  <button
                    className="session-item-button"
                    onClick={() => onSelectSession(session.id)}
                  >
                    <div className="session-item-content">
                      <span className="session-item-title">
                        {formatSessionTitle(session.createdAt)}
                      </span>
                      <span className="session-item-date">
                        {formatDate(session.createdAt)}
                      </span>
                    </div>
                    <span className="session-item-arrow">→</span>
                  </button>
                  <button
                    className="session-item-delete"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(session.id);
                    }}
                    aria-label="Delete session"
                    title="Delete session"
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="sessions-empty">No previous conversations</p>
          )}
        </div>
      </div>
    </div>
  );
}

