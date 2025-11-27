import { useEffect, useRef } from 'react';
import cibcLogo from '../assets/cibc_logo.svg';
import { Loader } from './common/Loader';
import './HomeView.css';

export function HomeView({ sessions, onCreateSession, onSelectSession, isLoading }) {
  const sessionsRef = useRef(null);
  const heroRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => {
      if (sessionsRef.current) {
        // Fade in sessions on scroll
        if (sessions.length > 0) {
          const scrolled = window.scrollY;
          const maxScroll = 300;
          const opacity = Math.min(scrolled / maxScroll, 1);
          sessionsRef.current.style.opacity = opacity;
        } else {
          sessionsRef.current.style.opacity = 0;
        }
      }

      // Update gradient on scroll
      if (heroRef.current) {
        const scrolled = window.scrollY;
        const maxScroll = 500; // Distance over which to fade
        const scrollProgress = Math.min(scrolled / maxScroll, 1);
        
        // Interpolate between light gray (#A8AAAC) and darker gray (#5A5D60)
        const startGray = { r: 168, g: 170, b: 172 }; // #A8AAAC
        const endGray = { r: 90, g: 93, b: 96 }; // #5A5D60 (darker gray)
        
        const currentGray = {
          r: Math.round(startGray.r + (endGray.r - startGray.r) * scrollProgress),
          g: Math.round(startGray.g + (endGray.g - startGray.g) * scrollProgress),
          b: Math.round(startGray.b + (endGray.b - startGray.b) * scrollProgress)
        };
        
        const grayColor = `rgb(${currentGray.r}, ${currentGray.g}, ${currentGray.b})`;
        heroRef.current.style.background = `linear-gradient(to bottom, var(--bg-primary, #ffffff), ${grayColor})`;
      }
    };

    // Set initial state
    if (sessionsRef.current) {
      if (sessions.length > 0) {
        sessionsRef.current.style.opacity = 0;
      } else {
        sessionsRef.current.style.opacity = 0;
      }
    }

    // Call once on mount
    handleScroll();
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [sessions.length]);

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString([], {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
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
                <button
                  key={session.id}
                  className="session-item"
                  onClick={() => onSelectSession(session.id)}
                >
                  <div className="session-item-content">
                    <span className="session-item-title">
                      Chat from {formatDate(session.createdAt)}
                    </span>
                    <span className="session-item-date">
                      {formatDate(session.createdAt)}
                    </span>
                  </div>
                  <span className="session-item-arrow">→</span>
                </button>
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

